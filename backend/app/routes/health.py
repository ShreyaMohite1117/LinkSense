from flask import Blueprint, jsonify

from app.extensions import cache, mongo
from app.ml import registry

bp = Blueprint("health", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    db_ok = True
    try:
        mongo.client.admin.command("ping") if not mongo.is_mock else None
    except Exception:  # noqa: BLE001
        db_ok = False
    return jsonify(
        status="ok" if db_ok else "degraded",
        database="mongomock (in-memory)" if mongo.is_mock else ("mongodb" if db_ok else "unreachable"),
        cache=cache.stats(),
        models_loaded=sorted(registry._models.keys()),
    ), (200 if db_ok else 503)
