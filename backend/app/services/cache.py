"""Small cache wrapper.

Uses Redis when it's reachable. If it isn't (common on a fresh Windows
machine) we drop back to an in-process dict so the app still runs -
redirects just won't be shared across workers.
"""
import json
import logging
import threading
import time

log = logging.getLogger(__name__)


class _MemoryStore:
    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def _alive(self, key):
        item = self._data.get(key)
        if not item:
            return None
        value, expires = item
        if expires and expires < time.time():
            self._data.pop(key, None)
            return None
        return item

    def get(self, key):
        with self._lock:
            item = self._alive(key)
            return item[0] if item else None

    def set(self, key, value, ex=None):
        with self._lock:
            self._data[key] = (value, time.time() + ex if ex else None)

    def delete(self, *keys):
        with self._lock:
            for k in keys:
                self._data.pop(k, None)

    def incr(self, key, ttl):
        with self._lock:
            item = self._alive(key)
            if item:
                value, expires = item
                self._data[key] = (value + 1, expires)
                return value + 1
            self._data[key] = (1, time.time() + ttl)
            return 1

    def ttl(self, key):
        with self._lock:
            item = self._alive(key)
            if not item or not item[1]:
                return -1
            return max(0, int(item[1] - time.time()))

    def flush(self):
        with self._lock:
            self._data.clear()


class Cache:
    def __init__(self):
        self.redis = None
        self.memory = _MemoryStore()
        self.default_ttl = 3600
        self.hits = 0
        self.misses = 0

    @property
    def backend(self):
        return "redis" if self.redis is not None else "memory"

    def init_app(self, app):
        self.default_ttl = app.config.get("CACHE_TTL_SECONDS", 3600)
        url = app.config.get("REDIS_URL")
        if not url:
            return
        try:
            import redis

            client = redis.Redis.from_url(url, socket_connect_timeout=1, decode_responses=True)
            client.ping()
            self.redis = client
            log.info("Connected to Redis at %s", url)
        except Exception as exc:  # noqa: BLE001 - any failure means "no redis"
            log.warning("Redis unavailable (%s) - using in-memory cache", exc)
            self.redis = None

    # --- json helpers -------------------------------------------------
    def get_json(self, key):
        raw = self._safe(lambda r: r.get(key), lambda m: m.get(key))
        if raw is None:
            self.misses += 1
            return None
        self.hits += 1
        return json.loads(raw)

    def set_json(self, key, value, ttl=None):
        raw = json.dumps(value, default=str)
        ttl = ttl or self.default_ttl
        self._safe(lambda r: r.set(key, raw, ex=ttl), lambda m: m.set(key, raw, ex=ttl))

    def delete(self, *keys):
        if keys:
            self._safe(lambda r: r.delete(*keys), lambda m: m.delete(*keys))

    def incr_window(self, key, ttl):
        """Increment a counter that expires `ttl` seconds after it's created."""

        def with_redis(r):
            count = r.incr(key)
            if count == 1:
                r.expire(key, ttl)
            return count

        return self._safe(with_redis, lambda m: m.incr(key, ttl))

    def ttl(self, key):
        return self._safe(lambda r: r.ttl(key), lambda m: m.ttl(key))

    def stats(self):
        total = self.hits + self.misses
        return {
            "backend": self.backend,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 3) if total else 0.0,
        }

    def _safe(self, redis_fn, memory_fn):
        if self.redis is not None:
            try:
                return redis_fn(self.redis)
            except Exception as exc:  # noqa: BLE001
                log.error("Redis error, falling back to memory: %s", exc)
        return memory_fn(self.memory)
