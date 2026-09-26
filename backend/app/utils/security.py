import secrets
from datetime import datetime, timezone
from functools import wraps

import jwt
from bson import ObjectId
from bson.errors import InvalidId
from flask import current_app, g, jsonify, request

from app.extensions import mongo


def utcnow():
    return datetime.now(timezone.utc)


def create_token(user_id, kind="access"):
    cfg = current_app.config
    lifetime = cfg["JWT_ACCESS_EXPIRES"] if kind == "access" else cfg["JWT_REFRESH_EXPIRES"]
    now = utcnow()
    payload = {
        "sub": str(user_id),
        "type": kind,
        "iat": now,
        "exp": now + lifetime,
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, cfg["JWT_SECRET"], algorithm="HS256")


def decode_token(token, expected="access"):
    payload = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
    if payload.get("type") != expected:
        raise jwt.InvalidTokenError("wrong token type")
    return payload


def generate_api_key():
    return "lsk_" + secrets.token_urlsafe(24)


def _user_from_request():
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return mongo.users.find_one({"api_key": api_key}), None

    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None, "Missing auth token"
    try:
        payload = decode_token(header[7:])
        user = mongo.users.find_one({"_id": ObjectId(payload["sub"])})
    except jwt.ExpiredSignatureError:
        return None, "Session expired"
    except (jwt.InvalidTokenError, InvalidId, KeyError):
        return None, "Invalid token"
    return user, None


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user, error = _user_from_request()
        if not user:
            return jsonify(error=error or "Invalid API key"), 401
        g.user = user
        return fn(*args, **kwargs)

    return wrapper


def optional_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user, _ = _user_from_request()
        g.user = user
        return fn(*args, **kwargs)

    return wrapper
