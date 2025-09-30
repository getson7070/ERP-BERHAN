# erp/db.py
from __future__ import annotations

import os
import json
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Optional, Tuple

import redis
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection, CursorResult

# -------------------------------------------------------------------
# Engine bootstrap & access
# -------------------------------------------------------------------

_ENGINE: Optional[Engine] = None


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        # Render/Heroku style config usually provides this. Fail loud if missing.
        raise RuntimeError("DATABASE_URL is not set")
    # SQLAlchemy prefers postgresql+psycopg2
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        # Pool settings are conservative to play nicely on Render
        _ENGINE = create_engine(
            _database_url(),
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=int(os.environ.get("DB_POOL_SIZE", "5")),
            max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "5")),
            future=True,
        )
    return _ENGINE


# -------------------------------------------------------------------
# Result wrapper giving a DB-API-ish interface that routes expect
# (description, fetchone, fetchall)
# -------------------------------------------------------------------

class _ResultWrapper:
    """
    Wrap SQLAlchemy CursorResult into a DB-API-like object with:
      - .description: sequence of (name,) tuples (the code expects desc[0])
      - .fetchone()  -> tuple | None
      - .fetchall()  -> list[tuple]
      - .keys()      -> list[str]
    """
    def __init__(self, result: CursorResult):
        self._result = result
        self._keys = list(result.keys())
        # mimic DB-API description shape used by the app: [ (colname,), ... ]
        self.description = [(k,) for k in self._keys]

    def keys(self):
        return list(self._keys)

    def fetchone(self) -> Optional[Tuple[Any, ...]]:
        row = self._result.fetchone()
        if row is None:
            return None
        return tuple(row)

    def fetchall(self) -> Iterable[Tuple[Any, ...]]:
        rows = self._result.fetchall()
        return [tuple(r) for r in rows]


# -------------------------------------------------------------------
# Connection wrapper that the app uses in routes
# -------------------------------------------------------------------

class _DBConnection(AbstractContextManager["_DBConnection"]):
    """
    Provides:
      - execute(text(sql), params) -> _ResultWrapper
      - commit()
      - close()
    Starts a transaction on open so commit() works as expected.
    """
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
        # open a fresh transaction for any subsequent statements
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
    """Return a DB connection wrapper (call .close() when done)."""
    return _DBConnection(get_engine())


# -------------------------------------------------------------------
# Redis client & helpers
# -------------------------------------------------------------------

@dataclass
class RedisClient:
    _client: Optional[redis.Redis] = None

    @classmethod
    def _url(cls) -> str:
        url = os.environ.get("REDIS_URL")
        if not url:
            raise RuntimeError("REDIS_URL is not set")
        return url

    @classmethod
    def client(cls) -> redis.Redis:
        if cls._client is None:
            cls._client = redis.from_url(cls._url(), decode_responses=False)
        return cls._client

    @classmethod
    def ensure_connection(cls) -> None:
        # a light ping to fail-fast on misconfig
        cls.client().ping()


# expose a bytes-based client to match existing code usage
redis_client: redis.Redis = RedisClient.client()


# -------------------------------------------------------------------
# First-run schema bootstrap
# -------------------------------------------------------------------

def ensure_schema(engine: Optional[Engine] = None) -> None:
    """
    Creates the minimal tables used by the app if they do not exist.
    This is idempotent and safe to call on every boot.
    """
    eng = engine or get_engine()
    with eng.begin() as conn:
        # Users table
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

        # WebAuthn credentials table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS webauthn_credentials (
                credential_id TEXT PRIMARY KEY,
                user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
                org_id TEXT,
                public_key BYTEA,
                sign_count INTEGER
            )
        """))

        # Regions & cities
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS regions_cities (
                region TEXT NOT NULL,
                city   TEXT NOT NULL
            )
        """))

        # Helpful indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_user_type ON users(user_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_org ON users(org_id)"))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_regions_cities_region
            ON regions_cities(region)
        """))


__all__ = [
    "get_engine",
    "get_db",
    "ensure_schema",
    "RedisClient",
    "redis_client",
]
