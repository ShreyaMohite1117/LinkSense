"""Lexical / host based features for the phishing classifier.

Everything here is computed from the URL string alone so scoring is instant
and doesn't need any network calls (no WHOIS, no page fetch).
"""
import ipaddress
import math
import re
from collections import Counter
from urllib.parse import unquote, urlparse

SUSPICIOUS_TLDS = {
    "tk", "ml", "ga", "cf", "gq", "xyz", "top", "zip", "click", "country", "kim",
    "work", "rest", "cam", "buzz", "icu", "live", "support", "monster", "loan", "mov",
}

SUSPICIOUS_WORDS = [
    "login", "log-in", "signin", "sign-in", "verify", "verification", "secure", "account",
    "update", "confirm", "banking", "password", "suspend", "unlock", "wallet", "billing",
    "invoice", "recover", "webscr", "authenticate", "validation", "limited", "urgent", "claim",
    "reward", "gift", "free", "bonus", "kyc", "refund",
]

BRANDS = [
    "paypal", "apple", "icloud", "google", "microsoft", "office365", "outlook", "amazon",
    "netflix", "facebook", "instagram", "whatsapp", "linkedin", "chase", "wellsfargo",
    "sbi", "hdfc", "icici", "axis", "paytm", "phonepe", "flipkart", "dropbox", "adobe",
    "coinbase", "binance", "metamask", "steam", "dhl", "fedex",
]

SHORTENERS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd", "buff.ly", "cutt.ly", "rb.gy"}

MULTI_PART_SUFFIXES = {"co.uk", "co.in", "org.in", "ac.in", "gov.in", "com.au", "co.jp", "com.br", "co.nz"}

FEATURE_NAMES = [
    "url_length", "host_length", "path_length", "query_length", "num_dots_host",
    "num_hyphens_host", "num_subdomains", "digit_ratio", "host_digit_ratio",
    "special_chars", "has_ip_host", "has_at", "double_slash_path", "uses_https",
    "has_port", "suspicious_tld", "suspicious_words", "brand_mismatch", "host_entropy",
    "is_shortener", "punycode", "path_depth", "risky_extension", "num_params",
    "encoded_chars",
]


def registered_domain(host):
    parts = host.lower().strip(".").split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in MULTI_PART_SUFFIXES:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _entropy(text):
    if not text:
        return 0.0
    counts = Counter(text)
    n = len(text)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _is_ip(host):
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return bool(re.fullmatch(r"0x[0-9a-f]+|\d{8,10}", host))


def extract(url):
    """Return a dict of named features for one URL."""
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "http://" + url
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""
    query = parsed.query or ""
    full = url.lower()
    decoded = unquote(full)

    reg = registered_domain(host) if host else ""
    reg_name = reg.split(".")[0]
    subdomain_part = host[: -len(reg)].rstrip(".") if reg and host.endswith(reg) else ""
    rest = subdomain_part + " " + path.lower() + " " + query.lower()

    brand_mismatch = 0
    for brand in BRANDS:
        if brand in rest and brand != reg_name:
            brand_mismatch = 1
            break
        # e.g. paypal-secure-login.com
        if brand in reg_name and reg_name != brand:
            brand_mismatch = 1
            break

    digits = sum(ch.isdigit() for ch in full)
    host_digits = sum(ch.isdigit() for ch in host)
    tld = host.rsplit(".", 1)[-1] if "." in host else ""

    return {
        "url_length": len(url),
        "host_length": len(host),
        "path_length": len(path),
        "query_length": len(query),
        "num_dots_host": host.count("."),
        "num_hyphens_host": host.count("-"),
        "num_subdomains": max(0, len(subdomain_part.split("."))) if subdomain_part else 0,
        "digit_ratio": digits / max(len(full), 1),
        "host_digit_ratio": host_digits / max(len(host), 1),
        "special_chars": sum(full.count(c) for c in "@~%=&!*$"),
        "has_ip_host": int(_is_ip(host)),
        "has_at": int("@" in parsed.netloc or "@" in path),
        "double_slash_path": int("//" in path),
        "uses_https": int(parsed.scheme == "https"),
        "has_port": int(_port(parsed) not in (None, 80, 443)),
        "suspicious_tld": int(tld in SUSPICIOUS_TLDS),
        "suspicious_words": sum(1 for w in SUSPICIOUS_WORDS if w in decoded),
        "brand_mismatch": brand_mismatch,
        "host_entropy": _entropy(host.replace(".", "")),
        "is_shortener": int(reg in SHORTENERS or host in SHORTENERS),
        "punycode": int("xn--" in host),
        "path_depth": len([p for p in path.split("/") if p]),
        "risky_extension": int(bool(re.search(r"\.(exe|scr|apk|zip|rar|js|php|cgi)(\?|$)", path.lower() + "?"))),
        "num_params": len([p for p in query.split("&") if p]),
        "encoded_chars": full.count("%"),
    }


def _port(parsed):
    try:
        return parsed.port
    except ValueError:
        return -1  # garbage port counts as suspicious


def vector(url):
    feats = extract(url)
    return [feats[name] for name in FEATURE_NAMES]


def explain(feats):
    """Human readable reasons behind a score - shown in the UI."""
    reasons = []
    if feats["has_ip_host"]:
        reasons.append("Uses a raw IP address instead of a domain name")
    if feats["brand_mismatch"]:
        reasons.append("Mentions a well-known brand that doesn't own this domain")
    if feats["suspicious_tld"]:
        reasons.append("Top-level domain is commonly abused for phishing")
    if feats["suspicious_words"] >= 2:
        reasons.append(f"Contains {feats['suspicious_words']} urgency / credential keywords (login, verify...)")
    elif feats["suspicious_words"] == 1:
        reasons.append("Contains a credential-related keyword")
    if feats["has_at"]:
        reasons.append("Has an '@' which can hide the real destination")
    if feats["num_subdomains"] >= 3:
        reasons.append("Unusually deep subdomain chain")
    if feats["num_hyphens_host"] >= 3:
        reasons.append("Many hyphens in the hostname")
    if feats["punycode"]:
        reasons.append("Punycode hostname (possible look-alike characters)")
    if feats["is_shortener"]:
        reasons.append("Points to another URL shortener, hiding the final destination")
    if feats["risky_extension"]:
        reasons.append("Links directly to an executable or script file")
    if not feats["uses_https"]:
        reasons.append("Not using HTTPS")
    if feats["url_length"] > 120:
        reasons.append("Very long URL")
    if feats["host_entropy"] > 3.9:
        reasons.append("Hostname looks randomly generated")
    return reasons
