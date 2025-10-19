import os
from contextlib import contextmanager
from typing import Optional, Any
from dataclasses import dataclass
import threading
import time

from sqlalchemy import create_engine, text  # type: ignore
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

def _normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        # Normalize deprecated scheme used by some providers
        return "postgresql+psycopg2://" + url.split("postgres://", 1)[1]
    return url

def get_engine(url: Optional[str] = None) -> Engine:
    url = _normalize_url(url or os.getenv("DATABASE_URL", "sqlite+pysqlite:///:memory:"))
    if url.startswith("sqlite"):
        # make sqlite memory/thread-friendly for tests
        connect_args = {"check_same_thread": False}
        kwargs = {"future": True, "echo": False, "connect_args": connect_args}
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
        return create_engine(url, **kwargs)
    return create_engine(url, future=True, echo=False)

@contextmanager
def get_db(url: Optional[str] = None):
    eng = get_engine(url)
    with eng.begin() as conn:
        yield conn

def get_dialect(url: Optional[str] = None) -> str:
    return get_engine(url).dialect.name

# -------- Minimal in-proc Redis shim used by tests & decorators --------
@dataclass
class _Entry:
    value: Any
    expire_at: Optional[float] = None

class _FakeRedis:
    def __init__(self):
        self._d = {}
        self._lock = threading.RLock()

    def _gc(self):
        now = time.time()
        rm = [k for k, v in self._d.items() if v.expire_at and v.expire_at <= now]
        for k in rm:
            self._d.pop(k, None)

    def set(self, key: str, value: Any, ex: Optional[int] = None):
        with self._lock:
            self._gc()
            self._d[key] = _Entry(value, time.time() + ex if ex else None)
            return True

    def setex(self, key: str, seconds: int, value: Any):
        return self.set(key, value, ex=seconds)

    def setnx(self, key: str, value: Any):
        with self._lock:
            self._gc()
            if key in self._d:
                return False
            self._d[key] = _Entry(value)
            return True

    def expire(self, key: str, seconds: int):
        with self._lock:
            if key in self._d:
                self._d[key].expire_at = time.time() + seconds
                return True
            return False

    def get(self, key: str):
        with self._lock:
            self._gc()
            e = self._d.get(key)
            return None if e is None else e.value

    def delete(self, key: str):
        with self._lock:
            self._d.pop(key, None)

    # queue helpers
    def rpush(self, key: str, value: Any):
        with self._lock:
            self._gc()
            q = self._d.setdefault(key, _Entry([])).value
            q.append(value)
            return len(q)

    def lpop(self, key: str):
        with self._lock:
            self._gc()
            q = self._d.get(key)
            if not q:
                return None
            if not q.value:
                return None
            return q.value.pop(0)

    def llen(self, key: str) -> int:
        with self._lock:
            self._gc()
            q = self._d.get(key)
            if not q or not isinstance(q.value, list):
                return 0
            return len(q.value)

    def incr(self, key: str, amount: int = 1) -> int:
        with self._lock:
            self._gc()
            cur = int(self.get(key) or 0) + amount
            self.set(key, cur)
            return cur

redis_client = _FakeRedis()
