# erp/db.py
from __future__ import annotations

import os
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple

import redis
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection, CursorResult

# ----------------------------- Engine --------------------------------

_ENGINE: Optional[Engine] = None

def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine(
            _database_url(),
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=int(os.environ.get("DB_POOL_SIZE", "5")),
            max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "5")),
            future=True,
        )
    return _ENGINE

# ------------------------- Result wrapper -----------------------------

class _ResultWrapper:
    def __init__(self, result: CursorResult):
        self._result = result
        self._keys = list(result.keys())
        self.description = [(k,) for k in self._keys]

    def keys(self):
        return list(self._keys)

    def fetchone(self) -> Optional[Tuple[Any, ...]]:
        row = self._result.fetchone()
        return None if row is None else tuple(row)

    def fetchall(self) -> Iterable[Tuple[Any, ...]]:
        return [tuple(r) for r in self._result.fetchall()]

# --------------------------- DB wrapper -------------------------------

class _DBConnection(AbstractContextManager["_DBConnection"]):
    def __init__(self, engine: Engine):
        self._engine = engine
        self._conn: Connection = engine.connect()
        self._trans = self._conn.begin()

    def execute(self, stmt, params: Optional[Dict[str, Any]] = None) -> _ResultWrapper:
        result = self._conn.execute(stmt, params or {})
        return _ResultWrapper(result)

    def commit(self) -> None:
        if self._trans.is_active:
            self._trans.commit()
        self._trans = self._conn.begin()

    def rollback(self) -> None:
        if self._trans.is_active:
            self._trans.rollback()
        self._trans = self._conn.begin()

    def close(self) -> None:
        try:
            if self._trans.is_active:
                self._trans.rollback()
        finally:
            self._conn.close()

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc is not None:
            self.rollback()
        else:
            self.commit()
        self.close()

def get_db() -> _DBConnection:
    return _DBConnection(get_engine())

# --------------------------- Redis (lazy) -----------------------------

class _InMemoryRedisStub:
    """Minimal stub so app can run without Redis. NOT shared across workers."""
    def __init__(self):
        self._store: Dict[bytes, bytes] = {}

    # Commonly used subset:
    def ping(self): return True
    def get(self, key: bytes) -> Optional[bytes]: return self._store.get(key)
    def set(self, key: bytes, value: bytes, ex: Optional[int] = None): self._store[key] = value; return True
    def setex(self, key: bytes, ttl: int, value: bytes): self._store[key] = value; return True
    def delete(self, *keys: bytes): 
        for k in keys: self._store.pop(k, None)
        return True

@dataclass
class RedisClient:
    _client: Optional[redis.Redis] = None
    _stub: Optional[_InMemoryRedisStub] = None

    @classmethod
    def client(cls):
        url = os.environ.get("REDIS_URL")
        if url:
            if cls._client is None:
                cls._client = redis.from_url(url, decode_responses=False)
            return cls._client
        # Fallback
        if cls._stub is None:
            cls._stub = _InMemoryRedisStub()
        return cls._stub

    @classmethod
    def ensure_connection(cls) -> None:
        # Only verify when real Redis is configured
        if os.environ.get("REDIS_URL"):
            cls.client().ping()

# Lazy: do NOT instantiate at import time
def get_redis():
    return RedisClient.client()

# ------------------------- Schema bootstrap ---------------------------

def ensure_schema(engine: Optional[Engine] = None) -> None:
    eng = engine or get_engine()
    with eng.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                user_type TEXT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password_hash TEXT,
                mfa_secret TEXT,
                permissions TEXT,
                approved_by_ceo BOOLEAN DEFAULT FALSE,
                hire_date DATE,
                salary NUMERIC,
                role TEXT,
                last_login TIMESTAMP,
                account_locked BOOLEAN DEFAULT FALSE,
                failed_attempts INTEGER DEFAULT 0,
                tin TEXT,
                institution_name TEXT,
                address TEXT,
                phone TEXT,
                region TEXT,
                city TEXT,
                org_id TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS webauthn_credentials (
                credential_id TEXT PRIMARY KEY,
                user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
                org_id TEXT,
                public_key BYTEA,
                sign_count INTEGER
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS regions_cities (
                region TEXT NOT NULL,
                city   TEXT NOT NULL
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_user_type ON users(user_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_org ON users(org_id)"))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_regions_cities_region
            ON regions_cities(region)
        """))

__all__ = ["get_engine", "get_db", "ensure_schema", "RedisClient", "get_redis"]
