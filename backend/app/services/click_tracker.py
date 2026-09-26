import hashlib
import ipaddress
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from flask import current_app, request
from user_agents import parse as parse_ua

from app.extensions import mongo
from app.services.rate_limiter import client_ip

BOT_PATTERN = re.compile(
    r"bot|crawl|spider|slurp|curl|wget|python-requests|httpx|axios|headless|phantom|scrapy|go-http",
    re.I,
)

REFERRER_NAMES = {
    "t.co": "twitter.com", "lnkd.in": "linkedin.com", "l.facebook.com": "facebook.com",
    "lm.facebook.com": "facebook.com", "l.instagram.com": "instagram.com", "wa.me": "whatsapp",
    "web.whatsapp.com": "whatsapp", "com.google.android.gm": "gmail", "mail.google.com": "gmail",
}


def hash_ip(ip):
    salt = current_app.config["SECRET_KEY"]
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()[:16]


def mask_ip(ip):
    """We never store full IPs - 49.36.122.8 -> 49.36.x.x"""
    if ":" in ip:
        return ip.split(":")[0] + ":x:x"
    parts = ip.split(".")
    return ".".join(parts[:2] + ["x", "x"]) if len(parts) == 4 else "hidden"


def guess_country(ip):
    # behind Cloudflare / most CDNs the country comes as a header, which is free and accurate
    for header in ("CF-IPCountry", "X-Country-Code", "X-Vercel-IP-Country"):
        val = request.headers.get(header)
        if val and val not in ("XX", "T1"):
            return val.upper()
    try:
        if ipaddress.ip_address(ip).is_private or ipaddress.ip_address(ip).is_loopback:
            return "Local"
    except ValueError:
        pass
    return "Unknown"


def referrer_domain(ref):
    if not ref:
        return "direct"
    host = (urlparse(ref).hostname or "").lower().replace("www.", "")
    return REFERRER_NAMES.get(host, host or "direct")


def describe_agent(ua_string):
    ua = parse_ua(ua_string or "")
    is_bot = bool(ua.is_bot or BOT_PATTERN.search(ua_string or "") or not ua_string)
    if ua.is_mobile:
        device = "Mobile"
    elif ua.is_tablet:
        device = "Tablet"
    elif ua.is_pc:
        device = "Desktop"
    else:
        device = "Other"
    return {
        "browser": ua.browser.family or "Other",
        "os": ua.os.family or "Other",
        "device": device,
        "is_bot": is_bot,
    }


def record_click(link, when=None):
    now = when or datetime.now(timezone.utc)
    ip = client_ip()
    ip_h = hash_ip(ip)
    agent = describe_agent(request.headers.get("User-Agent", ""))

    is_unique = mongo.clicks.find_one({"link_id": link["_id"], "ip_hash": ip_h}, {"_id": 1}) is None

    doc = {
        "link_id": link["_id"],
        "owner_id": link.get("owner_id"),
        "ts": now,
        # pre-bucketed keys make the time series aggregations trivial
        "day": now.strftime("%Y-%m-%d"),
        "hour_key": now.strftime("%Y-%m-%dT%H"),
        "ip_hash": ip_h,
        "ip_masked": mask_ip(ip),
        "country": guess_country(ip),
        "referrer_domain": referrer_domain(request.headers.get("Referer")),
        "language": (request.headers.get("Accept-Language") or "")[:5] or None,
        "unique": is_unique,
        **agent,
    }
    mongo.clicks.insert_one(doc)

    inc = {"clicks": 1}
    if is_unique:
        inc["unique_clicks"] = 1
    mongo.links.update_one({"_id": link["_id"]}, {"$inc": inc, "$set": {"last_clicked_at": now}})
    return doc
