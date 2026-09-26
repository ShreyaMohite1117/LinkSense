"""Shared handles (database + cache) that get wired up in create_app()."""
import logging

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from app.services.cache import Cache

log = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_mock = False

    def init_app(self, app):
        uri = app.config["MONGO_URI"]
        mode = str(app.config.get("USE_MOCK_DB", "auto")).lower()

        if mode in ("1", "true", "yes", "on"):
            self._use_mock()
        else:
            try:
                self._connect(uri)
            except ServerSelectionTimeoutError as exc:
                if mode == "auto":
                    log.warning("MongoDB not reachable at %s - falling back to in-memory database", uri)
                    self._use_mock()
                else:
                    raise RuntimeError(
                        f"Can't reach MongoDB at {uri}. Start MongoDB (or Docker), use a MongoDB Atlas URI, "
                        "or set USE_MOCK_DB=auto in backend/.env to run with an in-memory database."
                    ) from exc
        self._ensure_indexes()

    def _connect(self, uri):
        client = MongoClient(uri, serverSelectionTimeoutMS=3000, tz_aware=True)
        client.admin.command("ping")  # fail at boot, not on the first request
        self.client = client
        self.db = client.get_default_database(default="linksense")
        self.is_mock = False
        log.info("Connected to MongoDB")

    def _use_mock(self):
        import mongomock

        self.client = mongomock.MongoClient(tz_aware=True)
        self.db = self.client["linksense"]
        self.is_mock = True
        log.warning("Using in-memory database - data is lost when the server stops")

    def _ensure_indexes(self):
        self.db.users.create_index([("email", ASCENDING)], unique=True)
        self.db.users.create_index([("api_key", ASCENDING)], sparse=True)
        self.db.links.create_index([("short_code", ASCENDING)], unique=True)
        self.db.links.create_index([("owner_id", ASCENDING), ("created_at", DESCENDING)])
        self.db.clicks.create_index([("link_id", ASCENDING), ("ts", DESCENDING)])
        self.db.clicks.create_index([("owner_id", ASCENDING), ("ts", DESCENDING)])

    def __getattr__(self, item):
        # lets us write `mongo.links` instead of `mongo.db.links`
        if item in ("client", "db", "is_mock"):
            raise AttributeError(item)
        return self.db[item]


mongo = Database()
cache = Cache()
