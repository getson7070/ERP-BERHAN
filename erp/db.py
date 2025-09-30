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

    def close(self):
        self._conn.close()

def get_db() -> ConnShim:
    return ConnShim(engine.connect())

# Redis client with safe fallback (works with your CELERY_* or REDIS_URL settings)
class _MemoryTTL:
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._ttl: Dict[str, float] = {}
    def setex(self, key: str, ttl, value: str):
        seconds = int(getattr(ttl, "total_seconds", lambda: int(ttl))())
        self._store[key] = value
        self._ttl[key] = time.time() + seconds
    def get(self, key: str):
        if key in self._ttl and time.time() > self._ttl[key]:
            self._store.pop(key, None); self._ttl.pop(key, None); return None
        return self._store.get(key)
    def delete(self, key: str):
        self._store.pop(key, None); self._ttl.pop(key, None)

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
        redis_client = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)
        redis_client.setex("__healthcheck__", 5, "ok")
    except Exception:
        redis_client = _MemoryTTL()
else:
    redis_client = _MemoryTTL()
