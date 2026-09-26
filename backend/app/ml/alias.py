"""Readable alias suggestions pulled out of the destination URL.

https://medium.com/@dev/how-i-built-a-url-shortener-with-flask-3f2a
  -> built-url-shortener, url-shortener-flask, medium-url-shortener
"""
import re
from urllib.parse import unquote, urlparse

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "how", "i", "my",
    "is", "are", "was", "at", "by", "from", "this", "that", "www", "com", "html", "htm",
    "php", "index", "amp", "utm", "source", "medium", "campaign", "ref", "id", "page", "watch",
    "en", "us", "in", "org", "net", "http", "https", "s", "p", "q",
}


def _tokens(url):
    parsed = urlparse(url if "://" in url else "https://" + url)
    host = (parsed.hostname or "").replace("www.", "")
    site = host.split(".")[0] if host else ""
    # skip "@username" segments (medium, youtube handles) - they make poor aliases
    raw = "/".join(seg for seg in unquote(parsed.path).lower().split("/") if not seg.startswith("@"))
    words = re.split(r"[^a-z0-9]+", raw)
    words = [w for w in words if w and w not in STOPWORDS and not re.fullmatch(r"[0-9a-f]{6,}|\d+", w)]
    return site, words


def suggest(url, is_taken, limit=4):
    site, words = _tokens(url)
    candidates = []
    if len(words) >= 2:
        candidates.append("-".join(words[:3]))
        candidates.append("-".join(words[-2:]))
    if words:
        candidates.append(f"{site}-{words[0]}" if site else words[0])
        candidates.append("-".join(sorted(words, key=len, reverse=True)[:2]))
    if site:
        candidates.append(site)

    seen, out = set(), []
    for cand in candidates:
        cand = cand.strip("-")[:28]
        if len(cand) < 3 or cand in seen:
            continue
        seen.add(cand)
        final = cand
        n = 2
        while is_taken(final) and n < 20:
            final = f"{cand}-{n}"
            n += 1
        if not is_taken(final):
            out.append(final)
        if len(out) >= limit:
            break
    return out
