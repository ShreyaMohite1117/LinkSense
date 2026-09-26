import io
import time

import qrcode
from bson import ObjectId
from flask import Blueprint, current_app, jsonify, redirect, request, send_file
from qrcode.image.pil import PilImage
from werkzeug.security import check_password_hash

from app.extensions import cache, mongo
from app.services.click_tracker import record_click
from app.services.rate_limiter import rate_limit
from app.utils.serializers import as_aware, link_status
from app.utils.security import utcnow

bp = Blueprint("redirect", __name__)


def _load_link(code):
    """Cache-aside lookup. Counters aren't cached since they change on every click."""
    key = f"link:{code}"
    hit = cache.get_json(key)
    if hit is not None:
        if not hit:  # cached "not found" to stop repeated DB hits for junk codes
            return None, True
        hit["_id"] = ObjectId(hit["_id"])
        hit["owner_id"] = ObjectId(hit["owner_id"]) if hit.get("owner_id") else None
        for f in ("expires_at", "created_at"):
            if hit.get(f):
                hit[f] = _parse_dt(hit[f])
        return hit, True

    link = mongo.links.find_one({"short_code": code})
    if not link:
        cache.set_json(key, {}, ttl=60)
        return None, False
    slim = {
        "_id": str(link["_id"]),
        "owner_id": str(link["owner_id"]) if link.get("owner_id") else None,
        "short_code": link["short_code"],
        "original_url": link["original_url"],
        "password_hash": link.get("password_hash"),
        "expires_at": link.get("expires_at"),
        "max_clicks": link.get("max_clicks"),
        "is_active": link.get("is_active", True),
        "created_at": link.get("created_at"),
    }
    ttl = current_app.config["CACHE_TTL_SECONDS"]
    exp = as_aware(link.get("expires_at"))
    if exp:
        ttl = max(1, min(ttl, int((exp - utcnow()).total_seconds())))
    cache.set_json(key, slim, ttl=ttl)
    return link, False


def _parse_dt(value):
    from datetime import datetime

    return datetime.fromisoformat(value) if isinstance(value, str) else value


def _current_status(link):
    if link.get("max_clicks"):
        fresh = mongo.links.find_one({"_id": link["_id"]}, {"clicks": 1})
        link["clicks"] = fresh.get("clicks", 0) if fresh else 0
    return link_status(link)


@bp.get("/<code>")
def follow(code):
    started = time.perf_counter()
    frontend = current_app.config["FRONTEND_URL"]
    link, from_cache = _load_link(code)
    if not link:
        return redirect(f"{frontend}/not-found?code={code}", code=302)

    status = _current_status(link)
    if status != "active":
        return redirect(f"{frontend}/expired?reason={status}", code=302)
    if link.get("password_hash"):
        return redirect(f"{frontend}/p/{code}", code=302)

    record_click(link)
    resp = redirect(link["original_url"], code=302)
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Cache"] = "HIT" if from_cache else "MISS"
    resp.headers["X-Response-Time"] = f"{(time.perf_counter() - started) * 1000:.2f}ms"
    return resp


@bp.get("/api/r/<code>")
def link_info(code):
    """Public info the password / preview pages need. Never exposes the destination of a locked link."""
    link, _ = _load_link(code)
    if not link:
        return jsonify(error="Link not found"), 404
    status = _current_status(link)
    locked = bool(link.get("password_hash"))
    full = mongo.links.find_one({"_id": link["_id"]}, {"title": 1, "risk": 1})
    body = {
        "short_code": code,
        "status": status,
        "has_password": locked,
        "title": (full or {}).get("title"),
    }
    if not locked and status == "active":
        body["original_url"] = link["original_url"]
        body["risk"] = (full or {}).get("risk")
    return jsonify(body)


@bp.post("/api/r/<code>/unlock")
@rate_limit("RATE_LIMIT_AUTH", scope="unlock")
def unlock(code):
    link, _ = _load_link(code)
    if not link:
        return jsonify(error="Link not found"), 404
    status = _current_status(link)
    if status != "active":
        return jsonify(error="This link is no longer available", status=status), 410
    password = (request.get_json(silent=True) or {}).get("password") or ""
    if not link.get("password_hash") or not check_password_hash(link["password_hash"], password):
        return jsonify(error="Wrong password"), 401
    record_click(link)
    return jsonify(url=link["original_url"])


@bp.get("/api/qr/<code>")
def qr_code(code):
    link, _ = _load_link(code)
    if not link:
        return jsonify(error="Link not found"), 404
    fg = "#" + (request.args.get("fg") or "111827").lstrip("#")[:6]
    bg = "#" + (request.args.get("bg") or "ffffff").lstrip("#")[:6]
    size = min(20, max(4, request.args.get("scale", 10, type=int)))

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=size, border=2)
    qr.add_data(f"{current_app.config['BASE_URL']}/{code}")
    qr.make(fit=True)
    try:
        img = qr.make_image(image_factory=PilImage, fill_color=fg, back_color=bg)
    except ValueError:
        img = qr.make_image(image_factory=PilImage)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    as_download = request.args.get("download") == "1"
    return send_file(buf, mimetype="image/png", as_attachment=as_download, download_name=f"{code}-qr.png")
