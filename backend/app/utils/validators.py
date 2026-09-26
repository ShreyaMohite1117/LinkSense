import re
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
ALIAS_RE = re.compile(r"^[a-zA-Z0-9_-]{3,32}$")

# paths the app itself uses, so nobody can grab them as an alias
RESERVED_ALIASES = {
    "api", "admin", "login", "signup", "dashboard", "settings", "static",
    "health", "p", "expired", "scanner", "links", "docs", "favicon.ico",
}


def normalize_url(raw):
    """Add a scheme if the user forgot it and make sure it's something we can redirect to."""
    if not raw or not isinstance(raw, str):
        return None
    url = raw.strip()
    if len(url) > 2048:
        return None
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "https://" + url

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
    host = parsed.hostname or ""
    if not host or ("." not in host and host != "localhost"):
        return None
    return url


def valid_email(email):
    return bool(email and EMAIL_RE.match(email))


def password_problem(password):
    if not password or len(password) < 8:
        return "Password must be at least 8 characters"
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Password needs at least one letter and one number"
    return None


def alias_problem(alias):
    if not ALIAS_RE.match(alias):
        return "Alias must be 3-32 characters: letters, numbers, - or _"
    if alias.lower() in RESERVED_ALIASES:
        return "That alias is reserved"
    return None
