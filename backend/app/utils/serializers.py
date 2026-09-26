from datetime import datetime, timezone

from flask import current_app


def iso(dt):
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def as_aware(dt):
    """Mongo hands back naive datetimes (UTC). Make them comparable with utcnow()."""
    if dt and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def link_status(link, now=None):
    now = now or datetime.now(timezone.utc)
    if not link.get("is_active", True):
        return "disabled"
    exp = as_aware(link.get("expires_at"))
    if exp and exp <= now:
        return "expired"
    max_clicks = link.get("max_clicks")
    if max_clicks and link.get("clicks", 0) >= max_clicks:
        return "limit_reached"
    return "active"


def user_json(user):
    return {
        "id": str(user["_id"]),
        "name": user.get("name"),
        "email": user.get("email"),
        "created_at": iso(user.get("created_at")),
        "has_api_key": bool(user.get("api_key")),
    }


def link_json(link):
    base = current_app.config["BASE_URL"]
    return {
        "id": str(link["_id"]),
        "short_code": link["short_code"],
        "short_url": f"{base}/{link['short_code']}",
        "original_url": link["original_url"],
        "title": link.get("title"),
        "tags": link.get("tags", []),
        "clicks": link.get("clicks", 0),
        "unique_clicks": link.get("unique_clicks", 0),
        "is_active": link.get("is_active", True),
        "has_password": bool(link.get("password_hash")),
        "expires_at": iso(link.get("expires_at")),
        "max_clicks": link.get("max_clicks"),
        "risk": link.get("risk"),
        "status": link_status(link),
        "created_at": iso(link.get("created_at")),
        "last_clicked_at": iso(link.get("last_clicked_at")),
    }
