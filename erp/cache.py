import os
import json
import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
try:
    _client = redis.Redis.from_url(REDIS_URL)
    _client.ping()
except Exception:
    class _Dummy:
        def __init__(self):
            self.store = {}
        def get(self, k):
            v = self.store.get(k)
            return v
        def setex(self, k, ttl, v):
            self.store[k] = v
        def scan_iter(self, pattern):
            prefix = pattern.rstrip('*')
            for k in list(self.store.keys()):
                if k.startswith(prefix):
                    yield k
        def delete(self, k):
            self.store.pop(k, None)
    _client = _Dummy()


def cache_get(key: str):
    value = _client.get(key)
    return json.loads(value) if value else None


def cache_set(key: str, value, ttl: int = 300):
    _client.setex(key, ttl, json.dumps(value))


def cache_invalidate(pattern: str):
    for k in _client.scan_iter(pattern):
        _client.delete(k)
