import csv
import io
import re
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, Response, current_app, g, jsonify, request
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash

from app.extensions import cache, mongo
from app.ml import alias as alias_ml
from app.ml import phishing
from app.services.rate_limiter import rate_limit
from app.utils.security import login_required, utcnow
from app.utils.serializers import iso, link_json, link_status
from app.utils.shortcode import unique_code
from app.utils.validators import alias_problem, normalize_url

bp = Blueprint("links", __name__, url_prefix="/api/links")

MAX_BULK = 50


def _code_taken(code):
    return mongo.links.find_one({"short_code": code}, {"_id": 1}) is not None


def _own_link(link_id):
    try:
        oid = ObjectId(link_id)
    except (InvalidId, TypeError):
        return None
    return mongo.links.find_one({"_id": oid, "owner_id": g.user["_id"]})


def _parse_expiry(data):
    """Accepts either expires_at (ISO string) or expires_in_days. Returns (datetime|None, error|None)."""
    if data.get("expires_in_days") not in (None, ""):
        try:
            days = float(data["expires_in_days"])
        except (TypeError, ValueError):
            return None, "expires_in_days must be a number"
        if days <= 0 or days > 3650:
            return None, "Expiry must be between 1 hour and 10 years"
        return utcnow() + timedelta(days=days), None
    raw = data.get("expires_at")
    if not raw:
        return None, None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None, "expires_at must be an ISO date"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if dt <= utcnow():
        return None, "Expiry date must be in the future"
    return dt, None


def _parse_max_clicks(value):
    if value in (None, "", 0, "0"):
        return None, None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None, "max_clicks must be a whole number"
    if n < 1:
        return None, "max_clicks must be at least 1"
    return n, None


def _clean_tags(tags):
    if isinstance(tags, str):
        tags = tags.split(",")
    if not isinstance(tags, list):
        return []
    out = []
    for t in tags[:8]:
        t = str(t).strip().lower()[:24]
        if t and t not in out:
            out.append(t)
    return out


def create_link_for(user, data):
    """Shared by single create and bulk create. Returns (link_doc, risk, error, status_code)."""
    url = normalize_url(data.get("url"))
    if not url:
        return None, None, "Please enter a valid http(s) URL", 400
    if url.startswith(current_app.config["BASE_URL"]):
        return None, None, "That's already a LinkSense link", 400

    cfg = current_app.config
    risk = phishing.score_url(url, cfg["PHISHING_WARN_THRESHOLD"], cfg["PHISHING_BLOCK_THRESHOLD"])
    if risk["verdict"] == "malicious":
        mongo.blocked_urls.insert_one(
            {"owner_id": user["_id"], "url": url, "score": risk["score"], "ts": utcnow()}
        )
        return None, risk, "This URL looks like phishing, so we didn't shorten it.", 422

    expires_at, err = _parse_expiry(data)
    if err:
        return None, None, err, 400
    max_clicks, err = _parse_max_clicks(data.get("max_clicks"))
    if err:
        return None, None, err, 400

    alias = (data.get("alias") or "").strip()
    if alias:
        err = alias_problem(alias)
        if err:
            return None, None, err, 400
        if _code_taken(alias):
            return None, None, "That alias is already taken", 409
        code = alias
    else:
        code = unique_code(_code_taken)

    password = data.get("password") or ""
    if password and len(password) < 4:
        return None, None, "Link password must be at least 4 characters", 400

    link = {
        "owner_id": user["_id"],
        "short_code": code,
        "original_url": url,
        "title": (data.get("title") or "").strip()[:120] or None,
        "tags": _clean_tags(data.get("tags")),
        "custom_alias": bool(alias),
        "password_hash": generate_password_hash(password) if password else None,
        "expires_at": expires_at,
        "max_clicks": max_clicks,
        "is_active": True,
        "clicks": 0,
        "unique_clicks": 0,
        "risk": {"score": risk["score"], "verdict": risk["verdict"], "reasons": risk["reasons"][:4]},
        "created_at": utcnow(),
    }
    try:
        link["_id"] = mongo.links.insert_one(link).inserted_id
    except DuplicateKeyError:
        return None, None, "That alias is already taken", 409
    return link, risk, None, 201


@bp.post("")
@login_required
@rate_limit("RATE_LIMIT_SHORTEN", scope="shorten")
def create_link():
    data = request.get_json(silent=True) or {}
    link, risk, error, status = create_link_for(g.user, data)
    if error:
        body = {"error": error}
        if risk:
            body["risk"] = {k: risk[k] for k in ("score", "verdict", "reasons")}
        return jsonify(body), status
    out = link_json(link)
    if risk["verdict"] == "suspicious":
        out["warning"] = "This destination looks a bit risky. Double check before sharing."
    return jsonify(link=out), 201


@bp.post("/bulk")
@login_required
@rate_limit("RATE_LIMIT_SHORTEN", scope="shorten")
def bulk_create():
    data = request.get_json(silent=True) or {}
    urls = [u for u in (data.get("urls") or []) if isinstance(u, str) and u.strip()]
    if not urls:
        return jsonify(error="Send a list of URLs in `urls`"), 400
    if len(urls) > MAX_BULK:
        return jsonify(error=f"You can shorten up to {MAX_BULK} URLs at once"), 400

    results = []
    for raw in urls:
        link, risk, error, _ = create_link_for(g.user, {"url": raw, "tags": data.get("tags")})
        if error:
            results.append({"url": raw, "ok": False, "error": error})
        else:
            results.append({"url": raw, "ok": True, "link": link_json(link)})
    created = sum(1 for r in results if r["ok"])
    return jsonify(created=created, failed=len(results) - created, results=results), 201


@bp.get("")
@login_required
def list_links():
    page = max(1, request.args.get("page", 1, type=int))
    limit = min(100, max(1, request.args.get("limit", 10, type=int)))
    search = (request.args.get("search") or "").strip()
    status = request.args.get("status") or "all"
    sort = request.args.get("sort") or "newest"

    query = {"owner_id": g.user["_id"]}
    if search:
        rx = {"$regex": re.escape(search), "$options": "i"}
        query["$or"] = [{"original_url": rx}, {"short_code": rx}, {"title": rx}, {"tags": rx}]

    sort_spec = {
        "newest": [("created_at", -1)],
        "oldest": [("created_at", 1)],
        "clicks": [("clicks", -1), ("created_at", -1)],
    }.get(sort, [("created_at", -1)])

    docs = list(mongo.links.find(query).sort(sort_spec))
    if status != "all":
        now = utcnow()
        docs = [d for d in docs if link_status(d, now) == status]

    total = len(docs)
    page_docs = docs[(page - 1) * limit : page * limit]
    return jsonify(
        links=[link_json(d) for d in page_docs],
        total=total,
        page=page,
        pages=max(1, (total + limit - 1) // limit),
    )


@bp.get("/<link_id>")
@login_required
def get_link(link_id):
    link = _own_link(link_id)
    if not link:
        return jsonify(error="Link not found"), 404
    return jsonify(link=link_json(link))


@bp.patch("/<link_id>")
@login_required
def update_link(link_id):
    link = _own_link(link_id)
    if not link:
        return jsonify(error="Link not found"), 404
    data = request.get_json(silent=True) or {}
    changes, unset = {}, {}

    if "url" in data:
        url = normalize_url(data["url"])
        if not url:
            return jsonify(error="Please enter a valid http(s) URL"), 400
        cfg = current_app.config
        risk = phishing.score_url(url, cfg["PHISHING_WARN_THRESHOLD"], cfg["PHISHING_BLOCK_THRESHOLD"])
        if risk["verdict"] == "malicious":
            return jsonify(error="This URL looks like phishing, so we can't point the link there.",
                           risk={k: risk[k] for k in ("score", "verdict", "reasons")}), 422
        changes["original_url"] = url
        changes["risk"] = {"score": risk["score"], "verdict": risk["verdict"], "reasons": risk["reasons"][:4]}
    if "title" in data:
        changes["title"] = (data.get("title") or "").strip()[:120] or None
    if "tags" in data:
        changes["tags"] = _clean_tags(data.get("tags"))
    if "is_active" in data:
        changes["is_active"] = bool(data["is_active"])
    if "expires_at" in data or "expires_in_days" in data:
        if not data.get("expires_at") and not data.get("expires_in_days"):
            changes["expires_at"] = None
        else:
            exp, err = _parse_expiry(data)
            if err:
                return jsonify(error=err), 400
            changes["expires_at"] = exp
    if "max_clicks" in data:
        n, err = _parse_max_clicks(data.get("max_clicks"))
        if err:
            return jsonify(error=err), 400
        changes["max_clicks"] = n
    if "password" in data:
        pw = data.get("password") or ""
        if pw and len(pw) < 4:
            return jsonify(error="Link password must be at least 4 characters"), 400
        changes["password_hash"] = generate_password_hash(pw) if pw else None

    if not changes and not unset:
        return jsonify(error="Nothing to update"), 400
    changes["updated_at"] = utcnow()
    mongo.links.update_one({"_id": link["_id"]}, {"$set": changes})
    cache.delete(f"link:{link['short_code']}")
    return jsonify(link=link_json(mongo.links.find_one({"_id": link["_id"]})))


@bp.delete("/<link_id>")
@login_required
def delete_link(link_id):
    link = _own_link(link_id)
    if not link:
        return jsonify(error="Link not found"), 404
    mongo.links.delete_one({"_id": link["_id"]})
    mongo.clicks.delete_many({"link_id": link["_id"]})
    cache.delete(f"link:{link['short_code']}")
    return jsonify(message="Link deleted")


@bp.get("/suggest-alias")
@login_required
def suggest_alias():
    url = normalize_url(request.args.get("url"))
    if not url:
        return jsonify(suggestions=[])
    return jsonify(suggestions=alias_ml.suggest(url, _code_taken))


@bp.get("/check-alias")
@login_required
def check_alias():
    alias = (request.args.get("alias") or "").strip()
    err = alias_problem(alias)
    if err:
        return jsonify(available=False, reason=err)
    taken = _code_taken(alias)
    return jsonify(available=not taken, reason="Already taken" if taken else None)


@bp.get("/export")
@login_required
def export_links():
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["short_url", "original_url", "title", "clicks", "unique_clicks", "status", "created_at", "expires_at"])
    base = current_app.config["BASE_URL"]
    for link in mongo.links.find({"owner_id": g.user["_id"]}).sort("created_at", -1):
        writer.writerow([
            f"{base}/{link['short_code']}", link["original_url"], link.get("title") or "",
            link.get("clicks", 0), link.get("unique_clicks", 0), link_status(link),
            iso(link.get("created_at")), iso(link.get("expires_at")) or "",
        ])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=linksense-links.csv"},
    )
