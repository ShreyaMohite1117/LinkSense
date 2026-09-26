"""Fixed-window rate limiting backed by the shared cache (Redis if present)."""
from functools import wraps

from flask import current_app, g, jsonify, request

from app.extensions import cache

_UNITS = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}


def parse_limit(spec):
    """'30/minute' -> (30, 60)"""
    count, unit = spec.split("/")
    unit = unit.strip().rstrip("s")
    return int(count), _UNITS[unit]


def client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def rate_limit(config_key="RATE_LIMIT_DEFAULT", scope=None):
    def decorator(fn):
        bucket = scope or fn.__name__

        @wraps(fn)
        def wrapper(*args, **kwargs):
            limit, window = parse_limit(current_app.config[config_key])
            user = getattr(g, "user", None)
            who = f"u:{user['_id']}" if user else f"ip:{client_ip()}"
            key = f"rl:{bucket}:{who}"

            used = cache.incr_window(key, window)
            remaining = max(0, limit - used)
            if used > limit:
                retry = cache.ttl(key)
                resp = jsonify(error="Too many requests. Slow down a little.", retry_after=retry)
                resp.status_code = 429
                resp.headers["Retry-After"] = str(max(retry, 1))
                resp.headers["X-RateLimit-Limit"] = str(limit)
                resp.headers["X-RateLimit-Remaining"] = "0"
                return resp

            resp = current_app.make_response(fn(*args, **kwargs))
            resp.headers["X-RateLimit-Limit"] = str(limit)
            resp.headers["X-RateLimit-Remaining"] = str(remaining)
            return resp

        return wrapper

    return decorator
