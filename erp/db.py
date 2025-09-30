# erp/db.py
import os
import time
from typing import Any, Dict, Iterable, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection, CursorResult

# ---- SQLAlchemy engine (works for Postgres, MySQL, SQLite) ----
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{os.path.join(os.getcwd(), 'instance', 'erp.db')}"
engine: Engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)

# ---- Shim classes to satisfy both SQLAlchemy and DB-API-like expectations ----
class ResultShim:
    """
    Wraps a SQLAlchemy CursorResult to provide:
      - .fetchone() / .fetchall()
      - .description (list-of-tuples where desc[0] is column name)
    So legacy code that zips keys from .description keeps working.
    """
    def __init__(self, result: CursorResult):
        self._result = result
        # Snapshot rows because some callers iterate multiple times
        self._rows = self._result.fetchall()
        # shape [(name,)] because callers only read desc[0]
        self.description = [(name,) for name in self._result.keys()]

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    @property
    def keys(self):
        return list(self._result.keys())

class ConnShim:
    """
    Returns ResultShim from .execute() while still accepting SQLAlchemy text().
    Also exposes .close() to match expected lifecycle.
    """
    def __init__(self, conn: Connection):
        self._conn = conn

    def execute(self, stmt, params: Optional[Dict[str, Any]] = None) -> ResultShim:
        if params is None:
            res = self._conn.execute(stmt)
        else:
            res = self._conn.execute(stmt, params)
        return ResultShim(res)

    def close(self):
        self._conn.close()

# public API
def get_db() -> ConnShim:
    """
    Open a connection suitable for both SQLAlchemy 'text(...)' and legacy
    cursor-like expectations (description, fetchone, fetchall).
    Caller must .close().
    """
    conn = engine.connect()
    return ConnShim(conn)

# ---- Redis client with safe fallback ----------------------------------------
# If REDIS_URL is defined (recommended for prod), we use it.
# Otherwise we provide a minimal in-memory TTL store to avoid deploy crashes.
class _MemoryTTL:
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._ttl: Dict[str, float] = {}

    def setex(self, key: str, ttl, value: str):
        seconds = int(ttl.total_seconds()) if hasattr(ttl, "total_seconds") else int(ttl)
        self._store[key] = value
        self._ttl[key] = time.time() + seconds

    def get(self, key: str):
        if key in self._ttl and time.time() > self._ttl[key]:
            self._store.pop(key, None)
            self._ttl.pop(key, None)
            return None
        return self._store.get(key)

    def delete(self, key: str):
        self._store.pop(key, None)
        self._ttl.pop(key, None)

redis_client = None
REDIS_URL = os.getenv("REDIS_URL") or os.getenv("SOCKETIO_MESSAGE_QUEUE")  # allow reuse if set to redis://...
if REDIS_URL and REDIS_URL.startswith("redis://"):
    try:
        import redis  # type: ignore
        redis_client = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)
        # smoketest
        redis_client.setex("__healthcheck__", 5, "ok")
    except Exception:
        # fall back to memory if Redis lib or server not available
        redis_client = _MemoryTTL()
else:
    redis_client = _MemoryTTL()
