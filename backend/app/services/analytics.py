from datetime import datetime, timedelta, timezone

from app.extensions import cache, mongo
from app.ml import anomaly, forecaster
from app.utils.serializers import as_aware


def _group(match, field, limit=8):
    pipeline = [
        {"$match": match},
        {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    return [{"name": r["_id"] or "Unknown", "count": r["count"]} for r in mongo.clicks.aggregate(pipeline)]


def daily_series(match, days=30):
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=days - 1)
    counts = {r["name"]: r["count"] for r in _group({**match, "day": {"$gte": start.isoformat()}}, "day", limit=days + 1)}
    return [
        {"date": (start + timedelta(days=i)).isoformat(), "clicks": counts.get((start + timedelta(days=i)).isoformat(), 0)}
        for i in range(days)
    ]


def hourly_series(match, hours=24 * 7):
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(hours=hours - 1)
    counts = {
        r["name"]: r["count"]
        for r in _group({**match, "ts": {"$gte": start}}, "hour_key", limit=hours + 1)
    }
    series = []
    for i in range(hours):
        ts = start + timedelta(hours=i)
        series.append({"hour": ts.isoformat(), "clicks": counts.get(ts.strftime("%Y-%m-%dT%H"), 0)})
    return series, now


def peak_hour(match):
    rows = list(mongo.clicks.find(match, {"ts": 1}).sort("ts", -1).limit(5000))
    if not rows:
        return None
    buckets = [0] * 24
    for r in rows:
        buckets[as_aware(r["ts"]).hour] += 1
    return buckets


def link_forecast(link):
    series, last_hour = hourly_series({"link_id": link["_id"]})
    counts = [p["clicks"] for p in series]
    created = as_aware(link["created_at"])
    age_hours = max(1.0, (last_hour - created).total_seconds() / 3600)
    # don't feed hours from before the link existed as "zero traffic"
    usable = min(len(counts), int(age_hours) + 1)
    counts = counts[-usable:]
    fc = forecaster.forecast_next_hours(counts, last_hour, age_hours)
    return {"history": series[-48:], "forecast": fc, "summary": forecaster.summarize(counts, fc)}


def link_anomalies(link):
    key = f"anomaly:{link['_id']}:{link.get('clicks', 0)}"
    cached = cache.get_json(key)
    if cached:
        return cached
    clicks = list(
        mongo.clicks.find(
            {"link_id": link["_id"]},
            {"ts": 1, "ip_hash": 1, "ip_masked": 1, "is_bot": 1, "referrer_domain": 1,
             "device": 1, "browser": 1, "country": 1},
        ).sort("ts", -1).limit(3000)
    )
    result = anomaly.detect(clicks)
    cache.set_json(key, result, ttl=300)
    return result


def insights(link, stats, fc, anomalies):
    """Plain-English takeaways shown at the top of the analytics page."""
    notes = []
    total = link.get("clicks", 0)
    if total == 0:
        return ["No clicks yet - share the link and insights will show up here."]

    if stats["countries"]:
        top = stats["countries"][0]
        notes.append(f"{round(top['count'] / total * 100)}% of traffic comes from {top['name']}.")
    if stats["devices"]:
        top = stats["devices"][0]
        notes.append(f"{top['name']} is the main device ({round(top['count'] / total * 100)}% of clicks).")
    if stats["referrers"]:
        top = stats["referrers"][0]
        label = "Direct / unknown sources" if top["name"] == "direct" else top["name"]
        notes.append(f"{label} drives the most visits.")
    if stats.get("hour_buckets"):
        best = max(range(24), key=lambda h: stats["hour_buckets"][h])
        notes.append(f"Clicks peak around {best:02d}:00 UTC - a good time to reshare.")

    s = fc["summary"]
    if s["trend"] == "rising":
        notes.append(f"Forecast: traffic is rising (~{s['predicted_next_24h']:.0f} clicks expected in the next 24h).")
    elif s["trend"] == "falling":
        notes.append(f"Forecast: traffic is cooling off (~{s['predicted_next_24h']:.0f} clicks expected next 24h).")
    elif s["trend"] == "steady":
        notes.append(f"Forecast: steady traffic, around {s['predicted_next_24h']:.0f} clicks in the next 24h.")

    if anomalies.get("bot_rate", 0) > 0.1:
        notes.append(f"{round(anomalies['bot_rate'] * 100)}% of clicks look automated - real reach is lower than the raw count.")
    if anomalies.get("flagged"):
        notes.append(f"{anomalies['flagged']} clicks were flagged as anomalous by the Isolation Forest.")
    return notes


def link_stats(link):
    match = {"link_id": link["_id"]}
    stats = {
        "daily": daily_series(match),
        "countries": _group(match, "country"),
        "devices": _group(match, "device"),
        "browsers": _group(match, "browser"),
        "os": _group(match, "os"),
        "referrers": _group(match, "referrer_domain"),
        "hour_buckets": peak_hour(match),
        "bot_clicks": mongo.clicks.count_documents({**match, "is_bot": True}),
    }
    return stats


def overview(owner_id):
    match = {"owner_id": owner_id}
    links = list(mongo.links.find(match, {"clicks": 1, "unique_clicks": 1, "short_code": 1, "original_url": 1, "title": 1}))
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    top = sorted(links, key=lambda l: l.get("clicks", 0), reverse=True)[:5]
    return {
        "total_links": len(links),
        "total_clicks": sum(l.get("clicks", 0) for l in links),
        "unique_clicks": sum(l.get("unique_clicks", 0) for l in links),
        "clicks_last_7d": mongo.clicks.count_documents({**match, "ts": {"$gte": week_ago}}),
        "bot_clicks": mongo.clicks.count_documents({**match, "is_bot": True}),
        "blocked_links": mongo.blocked_urls.count_documents({"owner_id": owner_id}),
        "daily": daily_series(match, days=14),
        "top_links": [
            {"id": str(l["_id"]), "short_code": l["short_code"], "title": l.get("title") or l["original_url"],
             "clicks": l.get("clicks", 0)}
            for l in top
        ],
        "countries": _group(match, "country", limit=6),
        "devices": _group(match, "device", limit=4),
    }
