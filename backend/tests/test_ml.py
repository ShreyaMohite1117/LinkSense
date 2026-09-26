from datetime import datetime, timedelta, timezone

from app.ml import alias, anomaly, forecaster, phishing


def test_phishing_scores(app):
    bad = phishing.score_url("http://secure-paypal.com.login-verify.tk/webscr?cmd=login")
    good = phishing.score_url("https://github.com/pallets/flask")
    assert bad["score"] > good["score"]
    assert bad["verdict"] in ("suspicious", "malicious")
    assert good["verdict"] == "safe"


def test_trusted_domain_not_flagged(app):
    assert phishing.score_url("https://accounts.google.com/signin/v2/identifier")["verdict"] == "safe"


def test_forecast_shape(app):
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    history = [3, 5, 2, 8, 9, 4] * 8
    fc = forecaster.forecast_next_hours(history, now, age_hours=48)
    assert len(fc) == 24
    assert all(p["predicted"] >= 0 for p in fc)


def test_isolation_forest_catches_burst():
    now = datetime.now(timezone.utc)
    clicks = [
        {"ts": now - timedelta(hours=i), "ip_hash": f"ip{i}", "is_bot": False, "referrer_domain": "linkedin.com", "device": "Mobile"}
        for i in range(80)
    ]
    burst = [
        {"ts": now - timedelta(minutes=30, seconds=i), "ip_hash": "scraper", "is_bot": True, "referrer_domain": "direct", "device": "Other"}
        for i in range(15)
    ]
    result = anomaly.detect(clicks + burst)
    assert result["method"] == "isolation_forest"
    assert result["flagged"] > 0
    assert all(a["device"] == "Other" for a in result["anomalies"][:5])


def test_alias_suggestions():
    out = alias.suggest("https://medium.com/@dev/building-a-url-shortener-with-flask", lambda _: False)
    assert out and all(len(s) >= 3 for s in out)
