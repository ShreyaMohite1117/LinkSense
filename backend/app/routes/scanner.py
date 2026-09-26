from flask import Blueprint, current_app, jsonify, request

from app.extensions import mongo
from app.ml import phishing, registry
from app.services.rate_limiter import rate_limit
from app.utils.security import optional_auth, utcnow
from app.utils.validators import normalize_url

bp = Blueprint("scanner", __name__, url_prefix="/api")


@bp.post("/scan")
@optional_auth
@rate_limit("RATE_LIMIT_SHORTEN", scope="scan")
def scan():
    url = normalize_url((request.get_json(silent=True) or {}).get("url"))
    if not url:
        return jsonify(error="Please enter a valid http(s) URL"), 400
    cfg = current_app.config
    result = phishing.score_url(url, cfg["PHISHING_WARN_THRESHOLD"], cfg["PHISHING_BLOCK_THRESHOLD"])
    mongo.scans.insert_one({"url": url, "score": result["score"], "verdict": result["verdict"], "ts": utcnow()})
    return jsonify(url=url, **result)


@bp.get("/ml/models")
def model_info():
    phish = registry.metrics("phishing") or {}
    fc = registry.metrics("forecaster") or {}
    return jsonify(
        phishing={k: phish.get(k) for k in ("chosen_model", "dataset", "samples", "test_metrics", "all_models", "feature_importance", "trained_at")},
        forecaster={k: fc.get(k) for k in ("model", "train_rows", "mae_clicks_per_hour", "naive_mae_clicks_per_hour",
                                             "improvement_over_naive_pct", "feature_importance", "trained_at")},
        anomaly={"model": "IsolationForest", "fit": "per link, on its own click history", "contamination": 0.05},
        thresholds={"warn": current_app.config["PHISHING_WARN_THRESHOLD"], "block": current_app.config["PHISHING_BLOCK_THRESHOLD"]},
    )
