"""Fill the database with a demo account and realistic click history.

    python -m scripts.seed_demo            # add demo data (skips if it exists)
    python -m scripts.seed_demo --reset    # wipe the demo user and recreate

Login: demo@linksense.dev / Demo@1234
"""
import argparse
import hashlib
import random
from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

DEMO_EMAIL = "demo@linksense.dev"
DEMO_PASSWORD = "Demo@1234"

COUNTRIES = [("IN", 52), ("US", 14), ("GB", 7), ("DE", 5), ("CA", 4), ("SG", 4), ("AE", 4), ("AU", 3), ("NL", 2), ("JP", 2), ("FR", 3)]
REFERRERS = [("linkedin.com", 30), ("direct", 22), ("whatsapp", 16), ("twitter.com", 10), ("google.com", 9), ("github.com", 8), ("instagram.com", 5)]
AGENTS = [
    # (device, browser, os, weight)
    ("Mobile", "Chrome Mobile", "Android", 38),
    ("Desktop", "Chrome", "Windows", 24),
    ("Mobile", "Mobile Safari", "iOS", 14),
    ("Desktop", "Chrome", "Mac OS X", 8),
    ("Desktop", "Edge", "Windows", 5),
    ("Desktop", "Firefox", "Linux", 4),
    ("Tablet", "Safari", "iOS", 3),
    ("Mobile", "Samsung Internet", "Android", 4),
]

LINKS = [
    dict(code="linksense-repo", url="https://github.com/your-username/linksense", title="LinkSense source code",
         tags=["project", "github"], base=9.0, age_days=21),
    dict(code="portfolio", url="https://your-portfolio.vercel.app", title="My portfolio",
         tags=["personal"], base=5.0, age_days=18),
    dict(code="react-hooks", url="https://medium.com/@yourname/understanding-react-hooks-with-real-examples-4b2a",
         title="Blog: React hooks with real examples", tags=["blog"], base=3.0, age_days=12, burst=True),
    dict(code="hackathon-26", url="https://unstop.com/hackathons/smart-city-hackathon-2026",
         title="Smart City Hackathon registration", tags=["event"], base=6.0, age_days=6, expires_days=5, max_clicks=5000),
    dict(code="resume", url="https://drive.google.com/file/d/1AbCdEfGhIjKlMnOp/view", title="Resume (password protected)",
         tags=["personal"], base=1.2, age_days=9, password="resume2026"),
    dict(code=None, url="https://docs.python.org/3/library/asyncio.html", title="asyncio docs",
         tags=["reading"], base=0.6, age_days=4),
    dict(code="old-webinar", url="https://zoom.us/webinar/register/WN_example", title="Webinar (ended)",
         tags=["event"], base=2.0, age_days=16, expired=True),
]


def _weighted(rng, items):
    values = [i[:-1] if len(i) > 2 else i[0] for i in items]
    weights = [i[-1] for i in items]
    return rng.choices(values, weights=weights, k=1)[0]


def _hour_weight(hour):
    import math

    return 0.3 + 0.5 * math.exp(-((hour - 13) ** 2) / 8) + 1.0 * math.exp(-((hour - 20.5) ** 2) / 6)


def _click(rng, link, owner_id, ts, ip, agent=None, referrer=None, country=None, bot=False):
    device, browser, os_name = agent or _weighted(rng, AGENTS)
    return {
        "link_id": link["_id"],
        "owner_id": owner_id,
        "ts": ts,
        "day": ts.strftime("%Y-%m-%d"),
        "hour_key": ts.strftime("%Y-%m-%dT%H"),
        "ip_hash": hashlib.sha256(ip.encode()).hexdigest()[:16],
        "ip_masked": ".".join(ip.split(".")[:2] + ["x", "x"]),
        "country": country or _weighted(rng, COUNTRIES),
        "referrer_domain": referrer or _weighted(rng, REFERRERS),
        "language": "en-IN",
        "device": device,
        "browser": browser,
        "os": os_name,
        "is_bot": bot,
    }


def _random_ip(rng):
    return f"{rng.randint(11, 223)}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"


def seed(db, reset=False, seed_value=2026):
    rng = random.Random(seed_value)
    existing = db.users.find_one({"email": DEMO_EMAIL})
    if existing and not reset:
        return {"created": False, "email": DEMO_EMAIL}
    if existing:
        db.clicks.delete_many({"owner_id": existing["_id"]})
        db.links.delete_many({"owner_id": existing["_id"]})
        db.users.delete_one({"_id": existing["_id"]})

    now = datetime.now(timezone.utc)
    user = {
        "name": "Demo User",
        "email": DEMO_EMAIL,
        "password_hash": generate_password_hash(DEMO_PASSWORD),
        "created_at": now - timedelta(days=30),
    }
    user["_id"] = db.users.insert_one(user).inserted_id

    ip_pool = [_random_ip(rng) for _ in range(900)]
    total_clicks = 0
    for i, spec in enumerate(LINKS):
        created = now - timedelta(days=spec["age_days"], hours=rng.randint(0, 10))
        code = spec["code"] or f"k{rng.randint(10000, 99999)}"
        risk_reasons = []
        link = {
            "owner_id": user["_id"],
            "short_code": code,
            "original_url": spec["url"],
            "title": spec["title"],
            "tags": spec["tags"],
            "custom_alias": bool(spec["code"]),
            "password_hash": generate_password_hash(spec["password"]) if spec.get("password") else None,
            "expires_at": (now - timedelta(days=1)) if spec.get("expired")
            else (now + timedelta(days=spec["expires_days"])) if spec.get("expires_days") else None,
            "max_clicks": spec.get("max_clicks"),
            "is_active": True,
            "clicks": 0,
            "unique_clicks": 0,
            "risk": {"score": round(rng.uniform(0.01, 0.08), 3), "verdict": "safe", "reasons": risk_reasons},
            "created_at": created,
        }
        link["_id"] = db.links.insert_one(link).inserted_id

        end = link["expires_at"] if spec.get("expired") else now
        clicks = []
        hours = int((end - created).total_seconds() // 3600)
        for h in range(hours):
            ts_hour = created + timedelta(hours=h)
            # launch spike that decays, daily cycle, weekend dip
            rate = spec["base"] * _hour_weight(ts_hour.hour) * (1 + 6 * pow(2.718, -h / 30))
            if ts_hour.weekday() >= 5:
                rate *= 0.8
            n = _poisson(rng, rate / 4)
            for _ in range(n):
                ts = ts_hour + timedelta(seconds=rng.randint(0, 3599))
                # returning visitors: reuse some IPs
                ip = rng.choice(ip_pool[:120]) if rng.random() < 0.25 else rng.choice(ip_pool)
                bot = rng.random() < 0.03
                agent = ("Other", "Python Requests", "Other") if bot else None
                clicks.append(_click(rng, link, user["_id"], ts, ip, agent=agent, bot=bot))

        if spec.get("burst"):
            # a scraper hammering the link - this is what the Isolation Forest should catch
            burst_start = now - timedelta(days=2, hours=3)
            bad_ip = "185.220.101.44"
            for k in range(45):
                ts = burst_start + timedelta(seconds=k * rng.uniform(1.5, 3.5))
                clicks.append(_click(rng, link, user["_id"], ts, bad_ip,
                                     agent=("Other", "HeadlessChrome", "Linux"), referrer="direct",
                                     country="NL", bot=True))

        clicks.sort(key=lambda c: c["ts"])
        seen = set()
        for c in clicks:
            c["unique"] = c["ip_hash"] not in seen
            seen.add(c["ip_hash"])
        if clicks:
            db.clicks.insert_many(clicks)
        db.links.update_one(
            {"_id": link["_id"]},
            {"$set": {"clicks": len(clicks), "unique_clicks": len(seen),
                      "last_clicked_at": clicks[-1]["ts"] if clicks else None}},
        )
        total_clicks += len(clicks)

    return {"created": True, "email": DEMO_EMAIL, "links": len(LINKS), "clicks": total_clicks}


def _poisson(rng, lam):
    # Knuth - fine for the small rates we use here
    import math

    if lam <= 0:
        return 0
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    from app import create_app
    from app.extensions import mongo

    create_app()
    if mongo.is_mock:
        print("The app is using the in-memory database, which lives inside the server process.")
        print("Demo data is added automatically when the server starts, so there's nothing to do here.")
    else:
        result = seed(mongo.db, reset=args.reset)
        if result["created"]:
            print(f"Seeded {result['links']} links and {result['clicks']} clicks.")
        else:
            print("Demo user already exists (use --reset to recreate).")
        print(f"Login with {DEMO_EMAIL} / {DEMO_PASSWORD}")
