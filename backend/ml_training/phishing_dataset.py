"""Builds a labelled URL dataset for the phishing model.

The URLs are generated from patterns seen in public phishing feeds
(PhishTank / OpenPhish style) and from real, popular sites. It's good enough
to train a sensible lexical model offline. If you have a real dataset (e.g.
the Kaggle "Malicious URLs" or PhiUSIIL set) drop a CSV with `url,label`
columns at ml_training/data/urls.csv and train_phishing.py will use it instead.
"""
import random

LEGIT_DOMAINS = [
    "google.com", "youtube.com", "github.com", "stackoverflow.com", "wikipedia.org",
    "amazon.in", "amazon.com", "flipkart.com", "linkedin.com", "medium.com", "reddit.com",
    "microsoft.com", "apple.com", "netflix.com", "spotify.com", "nytimes.com", "bbc.co.uk",
    "thehindu.com", "ndtv.com", "timesofindia.indiatimes.com", "geeksforgeeks.org",
    "leetcode.com", "hackerrank.com", "coursera.org", "udemy.com", "kaggle.com", "python.org",
    "reactjs.org", "developer.mozilla.org", "docs.python.org", "npmjs.com", "pypi.org",
    "zomato.com", "swiggy.com", "irctc.co.in", "paytm.com", "hdfcbank.com", "icicibank.com",
    "onlinesbi.sbi", "myntra.com", "nykaa.com", "booking.com", "airbnb.com", "twitter.com",
    "x.com", "instagram.com", "facebook.com", "whatsapp.com", "notion.so", "figma.com",
    "dribbble.com", "behance.net", "dev.to", "hashnode.com", "vercel.com", "netlify.com",
    "cloud.google.com", "aws.amazon.com", "azure.microsoft.com", "openai.com", "anthropic.com",
    "espncricinfo.com", "cricbuzz.com", "imdb.com", "goodreads.com", "quora.com",
    "internshala.com", "naukri.com", "glassdoor.com", "indeed.com", "unstop.com",
    "iitb.ac.in", "iitd.ac.in", "nptel.ac.in", "ugc.gov.in", "india.gov.in", "mit.edu",
    "stanford.edu", "harvard.edu", "arxiv.org", "nature.com", "sciencedirect.com",
]

WORDS = [
    "react", "hooks", "tutorial", "python", "machine", "learning", "guide", "best", "laptops",
    "2025", "review", "news", "india", "cricket", "world", "cup", "recipe", "paneer", "travel",
    "goa", "tips", "career", "interview", "questions", "data", "science", "flask", "api",
    "design", "system", "startup", "funding", "budget", "phones", "under", "20000", "course",
    "free", "notes", "dsa", "arrays", "graphs", "docker", "kubernetes", "cloud", "resume",
    "template", "placement", "salary", "summer", "internship", "blog", "post", "how", "to",
    "build", "url", "shortener", "portfolio", "projects", "ideas", "movie", "song", "trailer",
]

PHISH_WORDS = [
    "login", "signin", "verify", "account", "secure", "update", "confirm", "banking",
    "password", "suspended", "unlock", "wallet", "billing", "recover", "webscr", "kyc",
    "refund", "reward", "claim", "gift", "support", "helpdesk", "auth", "session",
]

BRANDS = [
    "paypal", "apple", "icloud", "microsoft", "office365", "outlook", "amazon", "netflix",
    "facebook", "instagram", "sbi", "hdfc", "icici", "paytm", "phonepe", "flipkart",
    "coinbase", "binance", "metamask", "dhl", "fedex", "linkedin", "dropbox", "adobe",
]

BAD_TLDS = ["tk", "ml", "ga", "cf", "gq", "xyz", "top", "click", "live", "icu", "buzz", "support", "rest", "cam"]
PLAIN_TLDS = ["com", "net", "org", "info", "in", "co", "online", "site"]


def _slug(rng, lo=1, hi=5):
    return "-".join(rng.choice(WORDS) for _ in range(rng.randint(lo, hi)))


def _rand_token(rng, n):
    return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(n))


def legit_url(rng):
    domain = rng.choice(LEGIT_DOMAINS)
    if rng.random() < 0.2 and domain.count(".") == 1:
        domain = rng.choice(["www.", "blog.", "docs.", "m.", "en."]) + domain
    scheme = "https" if rng.random() < 0.93 else "http"
    style = rng.random()
    if style < 0.3:
        path = "/" + _slug(rng, 2, 7)
    elif style < 0.5:
        path = f"/{rng.choice(WORDS)}/{_slug(rng, 1, 4)}-{rng.randint(1000, 999999)}"
    elif style < 0.65:
        path = f"/watch?v={_rand_token(rng, 11)}"
    elif style < 0.8:
        path = f"/{rng.choice(WORDS)}/{rng.choice(WORDS)}/"
    elif style < 0.9:
        path = f"/search?q={'+'.join(rng.choice(WORDS) for _ in range(rng.randint(1, 4)))}"
    else:
        path = ""
    if rng.random() < 0.15:
        sep = "&" if "?" in path else "?"
        path += f"{sep}utm_source={rng.choice(['twitter', 'linkedin', 'newsletter'])}&utm_medium=social"
    return f"{scheme}://{domain}{path}"


def phishing_url(rng):
    brand = rng.choice(BRANDS)
    kw = rng.choice(PHISH_WORDS)
    kw2 = rng.choice(PHISH_WORDS)
    tld = rng.choice(BAD_TLDS if rng.random() < 0.55 else PLAIN_TLDS)
    scheme = "https" if rng.random() < 0.45 else "http"
    pattern = rng.randint(0, 9)

    if pattern == 0:  # brand in subdomain
        host = f"{brand}.com.{kw}-{_rand_token(rng, 5)}.{tld}"
        path = f"/{kw2}/index.php"
    elif pattern == 1:  # hyphenated look-alike
        host = f"{brand}-{kw}-{kw2}.{tld}"
        path = f"/{_rand_token(rng, 8)}"
    elif pattern == 2:  # raw IP
        host = ".".join(str(rng.randint(1, 254)) for _ in range(4))
        path = f"/{brand}/{kw}.html"
    elif pattern == 3:  # @ trick
        host = f"{brand}.com@{_rand_token(rng, 7)}.{tld}"
        path = f"/{kw}"
    elif pattern == 4:  # random host, brand in path
        host = f"{_rand_token(rng, rng.randint(8, 14))}.{tld}"
        path = f"/{brand}/{kw}/{kw2}?session={_rand_token(rng, 24)}"
    elif pattern == 5:  # compromised wordpress-ish site
        host = f"{rng.choice(WORDS)}{rng.choice(WORDS)}.{rng.choice(PLAIN_TLDS)}"
        path = f"/wp-content/plugins/{_rand_token(rng, 6)}/{brand}/{kw}.php"
    elif pattern == 6:  # deep subdomains
        host = f"{kw}.{brand}.{kw2}.{_rand_token(rng, 4)}.{tld}"
        path = "/"
    elif pattern == 7:  # typosquat
        typo = brand.replace("a", "4", 1).replace("o", "0", 1).replace("l", "1", 1)
        host = f"www.{typo}{rng.choice(['', '-' + kw])}.{tld}"
        path = f"/{kw}"
    elif pattern == 8:  # encoded redirect
        host = f"{_rand_token(rng, 10)}.{tld}"
        path = f"/r?u=http%3A%2F%2F{brand}-{kw}.{tld}%2F{kw2}&id={rng.randint(10000, 99999)}"
    else:  # free hosting / file drop
        host = f"{brand}-{kw}{rng.randint(1, 999)}.{rng.choice(['web.app', 'firebaseapp.com', 'weebly.com', '000webhostapp.com'])}"
        path = f"/{kw2}.html"
    return f"{scheme}://{host}{path}"


def hard_legit(rng):
    """Legit URLs that *look* a bit scary, so the model can't cheat on keywords."""
    templates = [
        "https://accounts.google.com/signin/v2/identifier?service=mail",
        "https://www.paypal.com/in/signin",
        "https://login.microsoftonline.com/common/oauth2/authorize",
        "https://www.amazon.in/ap/signin?openid.return_to=https%3A%2F%2Fwww.amazon.in",
        "https://retail.onlinesbi.sbi/retail/login.htm",
        "https://netbanking.hdfcbank.com/netbanking/",
        "https://appleid.apple.com/account/manage",
        "https://github.com/login?return_to=%2Fsettings%2Fsecurity",
        "https://www.linkedin.com/checkpoint/challenge/verify",
        "https://support.apple.com/en-in/HT201355",
    ]
    return rng.choice(templates)


def hard_phish(rng):
    """Phishing that looks fairly clean."""
    brand = rng.choice(BRANDS)
    return f"https://{brand}{rng.choice(['help', 'care', 'online', 'service'])}.{rng.choice(PLAIN_TLDS)}/"


def build(n=12000, seed=42, label_noise=0.02):
    rng = random.Random(seed)
    rows = []
    for _ in range(n // 2):
        rows.append((legit_url(rng) if rng.random() > 0.08 else hard_legit(rng), 0))
        rows.append((phishing_url(rng) if rng.random() > 0.08 else hard_phish(rng), 1))
    # real feeds are never perfectly labelled
    rows = [(u, 1 - y) if rng.random() < label_noise else (u, y) for u, y in rows]
    rng.shuffle(rows)
    return rows
