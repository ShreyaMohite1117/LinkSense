import numpy as np

from app.ml import registry, url_features

# big, well known sites we never want to flag just because the URL has "login" in it
TRUSTED_DOMAINS = {
    "google.com", "youtube.com", "github.com", "microsoft.com", "microsoftonline.com", "apple.com",
    "amazon.com", "amazon.in", "paypal.com", "linkedin.com", "facebook.com", "instagram.com",
    "wikipedia.org", "stackoverflow.com", "netflix.com", "hdfcbank.com", "icicibank.com",
    "onlinesbi.sbi", "sbi.co.in", "flipkart.com", "twitter.com", "x.com", "reddit.com",
}


def score_url(url, warn_at=0.5, block_at=0.8):
    feats = url_features.extract(url)
    bundle = registry.get("phishing")
    vec = np.array([[feats[n] for n in bundle["features"]]], dtype=float)
    prob = float(bundle["model"].predict_proba(vec)[0][1])

    from urllib.parse import urlparse

    host = (urlparse(url if "://" in url else "http://" + url).hostname or "").lower()
    domain = url_features.registered_domain(host) if host else ""
    trusted = domain in TRUSTED_DOMAINS
    if trusted:
        prob = min(prob, 0.05)

    if prob >= block_at:
        verdict = "malicious"
    elif prob >= warn_at:
        verdict = "suspicious"
    else:
        verdict = "safe"

    return {
        "score": round(prob, 4),
        "verdict": verdict,
        "domain": domain,
        "trusted_domain": trusted,
        "reasons": [] if trusted else url_features.explain(feats),
        "features": feats,
    }
