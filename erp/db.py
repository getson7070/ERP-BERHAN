# erp/db.py
import os
import time
from typing import Any, Dict, Optional

from sqlalchemy import create_engine, text  # noqa: F401
from sqlalchemy.engine import Engine, Connection, CursorResult

INSTANCE_DIR = os.path.join(os.getcwd(), "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{os.path.join(INSTANCE_DIR, 'erp.db')}"
engine: Engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)

class ResultShim:
    def __init__(self, result: CursorResult):
        self._result = result
        self._rows = self._result.fetchall()
        self.description = [(name,) for name in self._result.keys()]

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

class ConnShim:
    def __init__(self, conn: Connection):
        self._conn = conn

    def execute(self, stmt, params: Optional[Dict[str, Any]] = None) -> ResultShim:
        res = self._conn.execute(stmt, params or {})
        return ResultShim(res)

    def commit(self):
        try:
            self._conn.commit()
        except Exception:
            # Some DBs/engines autocommit reads; no-op is fine here.
            pass

    def rollback(self):
        try:
            self._conn.rollback()
        except Exception:
            pass

    def close(self):
        self._conn.close()

def get_db() -> ConnShim:
    return ConnShim(engine.connect())

# -------- Redis (or in-memory) client ----------
class _MemoryTTL:
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._ttl: Dict[str, float] = {}

    def _expired(self, key: str) -> bool:
        if key in self._ttl and time.time() > self._ttl[key]:
            self._store.pop(key, None)
            self._ttl.pop(key, None)
            return True
        return False

    def setex(self, key: str, ttl, value: Any):
        seconds = int(ttl.total_seconds()) if hasattr(ttl, "total_seconds") else int(ttl)
        self._store[key] = value
        self._ttl[key] = time.time() + seconds

    def get(self, key: str):
        if self._expired(key):
            return None
        return self._store.get(key)

    def delete(self, key: str):
        self._store.pop(key, None)
        self._ttl.pop(key, None)
        return 1

    # Methods used by auth.py
    def exists(self, key: str) -> int:
        if self._expired(key):
            return 0
        return 1 if key in self._store else 0

    def ttl(self, key: str) -> int:
        if self._expired(key) or key not in self._ttl:
            return -2  # Redis style: key does not exist
        remaining = int(self._ttl[key] - time.time())
        return remaining if remaining >= 0 else -2

    def incr(self, key: str) -> int:
        if self._expired(key):
            self._store.pop(key, None)
        val = self._store.get(key, 0)
        try:
            val = int(val)
        except Exception:
            val = 0
        val += 1
        self._store[key] = val
        # no TTL unless previously set
        return val

    def expire(self, key: str, seconds: int):
        if key in self._store:
            self._ttl[key] = time.time() + int(seconds)
            return 1
        return 0

redis_client = None
REDIS_URL = (
    os.getenv("REDIS_URL")
    or os.getenv("SOCKETIO_MESSAGE_QUEUE")
    or os.getenv("CELERY_BROKER_URL")
    or os.getenv("CELERY_RESULT_BACKEND")
)
if REDIS_URL and REDIS_URL.startswith("redis://"):
    try:
        import redis  # type: ignore
        # decode_responses=True returns str (not bytes) which is safer in Flask apps
        redis_client = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)
        redis_client.setex("__healthcheck__", 5, "ok")
    except Exception:
        redis_client = _MemoryTTL()
else:
    redis_client = _MemoryTTL()
