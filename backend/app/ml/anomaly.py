"""Click-level anomaly detection with Isolation Forest.

The model is fit on each link's own clicks, so "normal" is relative to how
that link is actually used. Anything the forest isolates quickly (burst from
one IP, headless browser at 4 AM with no referrer, ...) gets flagged.
"""
import math
from collections import defaultdict

import numpy as np
from sklearn.ensemble import IsolationForest

from app.utils.serializers import as_aware

MIN_CLICKS_FOR_MODEL = 25


def _features(clicks):
    """clicks must be sorted by time ascending."""
    by_ip = defaultdict(list)
    for c in clicks:
        by_ip[c.get("ip_hash") or "?"].append(as_aware(c["ts"]).timestamp())

    total = len(clicks)
    rows = []
    last_seen = {}
    for c in clicks:
        ip = c.get("ip_hash") or "?"
        t = as_aware(c["ts"]).timestamp()
        times = by_ip[ip]
        # clicks from the same IP within +-60s
        burst = sum(1 for x in times if abs(x - t) <= 60)
        gap = t - last_seen[ip] if ip in last_seen else 86400.0
        last_seen[ip] = t
        hour = as_aware(c["ts"]).hour
        rows.append([
            math.log1p(burst),
            math.log1p(max(gap, 0)),
            len(times) / total,
            1.0 if c.get("is_bot") else 0.0,
            0.0 if c.get("referrer_domain") and c["referrer_domain"] != "direct" else 1.0,
            math.sin(2 * math.pi * hour / 24),
            math.cos(2 * math.pi * hour / 24),
            1.0 if c.get("device") == "Other" else 0.0,
        ])
    return np.array(rows), by_ip


def _reasons(click, row):
    reasons = []
    if click.get("is_bot"):
        reasons.append("Bot / automated user agent")
    if row[0] >= math.log1p(5):
        reasons.append(f"Burst of {int(round(math.expm1(row[0])))} clicks from one IP within a minute")
    if row[1] < math.log1p(3):
        reasons.append("Repeat click seconds after the previous one")
    if row[2] > 0.3:
        reasons.append("Single IP responsible for a large share of traffic")
    if not reasons:
        reasons.append("Unusual combination of time, source and device")
    return reasons


def detect(clicks, contamination=0.05):
    clicks = sorted(clicks, key=lambda c: as_aware(c["ts"]))
    total = len(clicks)
    if total == 0:
        return {"method": "none", "total": 0, "anomalies": [], "anomaly_rate": 0.0, "bot_rate": 0.0}

    X, by_ip = _features(clicks)
    bot_rate = float(X[:, 3].mean())

    if total < MIN_CLICKS_FOR_MODEL:
        # not enough data to learn what "normal" is - use simple rules
        flagged = [i for i, r in enumerate(X) if r[3] == 1.0 or r[0] >= math.log1p(5)]
        scores = {i: 1.0 for i in flagged}
        method = "rules"
    else:
        forest = IsolationForest(n_estimators=150, contamination=contamination, random_state=42)
        labels = forest.fit_predict(X)
        raw = -forest.score_samples(X)  # higher = more anomalous
        flagged = [i for i, lab in enumerate(labels) if lab == -1]
        lo, hi = float(raw.min()), float(raw.max())
        scores = {i: (raw[i] - lo) / (hi - lo) if hi > lo else 1.0 for i in flagged}
        method = "isolation_forest"

    anomalies = []
    for i in sorted(flagged, key=lambda k: -scores[k])[:50]:
        c = clicks[i]
        anomalies.append({
            "ts": as_aware(c["ts"]).isoformat(),
            "ip": c.get("ip_masked", "hidden"),
            "country": c.get("country", "Unknown"),
            "device": c.get("device"),
            "browser": c.get("browser"),
            "referrer": c.get("referrer_domain", "direct"),
            "score": round(float(scores[i]), 3),
            "reasons": _reasons(c, X[i]),
        })

    top_ips = sorted(by_ip.items(), key=lambda kv: -len(kv[1]))[:1]
    return {
        "method": method,
        "total": total,
        "flagged": len(flagged),
        "anomaly_rate": round(len(flagged) / total, 4),
        "bot_rate": round(bot_rate, 4),
        "top_ip_share": round(len(top_ips[0][1]) / total, 4) if top_ips else 0.0,
        "anomalies": anomalies,
    }
