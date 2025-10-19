from __future__ import annotations
import os, sqlite3
from types import SimpleNamespace
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import redis as _redis

_ENGINE: Engine | None = None

def _db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    path = os.getenv("DATABASE_PATH", "app.db")
    return f"sqlite:///{path}"

def get_engine() -> Engine:
    global _ENGINE
    url = _db_url()
    if _ENGINE is None or str(_ENGINE.url) != url:
        _ENGINE = create_engine(url, future=True)
    return _ENGINE

class _DBWrapper:
    """Make sqlite3.Connection look a bit like SA Connection for tests."""
    def __init__(self, conn: sqlite3.Connection, dialect_name: str = "sqlite"):
        self._conn = conn
        self._dialect = SimpleNamespace(name=dialect_name)  # used by tests to skip
    def execute(self, *a, **k): return self._conn.execute(*a, **k)
    def cursor(self, *a, **k): return self._conn.cursor(*a, **k)
    def commit(self): return self._conn.commit()
    def close(self): return self._conn.close()

def get_db():
    """Return a connection tests can call .execute()/.cursor() on.

    - If DATABASE_URL starts with postgresql -> return SQLAlchemy Connection
    - Else -> return sqlite3.Connection wrapped with a small adapter
    """
    url = os.getenv("DATABASE_URL")
    if url and url.startswith("postgresql"):
        return get_engine().connect()
    path = os.getenv("DATABASE_PATH", "app.db")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return _DBWrapper(conn, "sqlite")

# ----------------- Redis -----------------
class _FakeRedis:
    def __init__(self): self._data = {}
    def ping(self): return True
    def set(self, k, v): self._data[k] = v
    def get(self, k): return self._data.get(k)
    def delete(self, k): self._data.pop(k, None)
    def rpush(self, k, v): self._data.setdefault(k, []).append(v)
    def lrange(self, k, start, end):
        arr = self._data.get(k, [])
        if end == -1: end = len(arr) - 1
        return arr[start:end+1]

USE_FAKE = os.getenv("USE_FAKE_REDIS") == "1"

try:
    if USE_FAKE:
        redis_client = _FakeRedis()
    else:
        rc = _redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        rc.ping()
        redis_client = rc
except Exception:
    # Provide a handle that raises at use (what the fail-fast test expects)
    class _FailRedis:
        def __getattr__(self, _):
            def _boom(*a, **k):
                raise RuntimeError("Redis unavailable")
            return _boom
    redis_client = _FailRedis()

def get_dialect() -> str:
    """Return the DB dialect name ('postgresql', 'sqlite', etc.) without touching network."""
    url = _db_url().lower()
    # Handle most common schemes quickly
    for prefix in ("postgresql", "mysql", "sqlite", "mssql", "oracle"):
        if url.startswith(prefix):
            return "postgresql" if prefix.startswith("postgres") else prefix
    # Fallback: ask SQLAlchemy to parse
    try:
        return create_engine(url, future=True).dialect.name
    except Exception:
        return "unknown"


