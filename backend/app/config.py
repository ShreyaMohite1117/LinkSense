import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _bool(name, default=False):
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    JWT_SECRET = os.getenv("JWT_SECRET", SECRET_KEY)
    JWT_ACCESS_EXPIRES = timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "60")))
    JWT_REFRESH_EXPIRES = timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7")))

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/linksense")
    # "auto"  -> use MongoDB, fall back to an in-memory mock if it isn't running
    # "true"  -> always in-memory (data resets on restart)
    # "false" -> MongoDB only, refuse to start without it
    USE_MOCK_DB = os.getenv("USE_MOCK_DB", "auto").strip().lower()

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

    # the public base used when building short links, e.g. https://lnks.io
    BASE_URL = os.getenv("BASE_URL", "http://localhost:5000").rstrip("/")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", FRONTEND_URL).split(",") if o.strip()]

    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "120/minute")
    RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "10/minute")
    RATE_LIMIT_SHORTEN = os.getenv("RATE_LIMIT_SHORTEN", "30/minute")

    # links scoring above this are refused when created
    PHISHING_BLOCK_THRESHOLD = float(os.getenv("PHISHING_BLOCK_THRESHOLD", "0.80"))
    PHISHING_WARN_THRESHOLD = float(os.getenv("PHISHING_WARN_THRESHOLD", "0.50"))

    # load the demo account automatically when running on the in-memory database
    SEED_DEMO = _bool("SEED_DEMO", True)

    TESTING = False


class TestConfig(Config):
    TESTING = True
    USE_MOCK_DB = "true"
    REDIS_URL = ""
    RATE_LIMIT_AUTH = "1000/minute"
    RATE_LIMIT_SHORTEN = "1000/minute"
    RATE_LIMIT_DEFAULT = "1000/minute"
