"""Database helpers for the ERP application.

This module was originally written for a SQLite-only setup. The
application has since moved to PostgreSQL with SQLAlchemy, but the test
suite still patches ``DATABASE_PATH`` to point to a temporary SQLite
file. To support both scenarios, the engine is created on demand based
on the current environment variables instead of at import time. This
mirrors production behaviour while letting the tests supply a SQLite
path without needing a running PostgreSQL server.

Connection pooling parameters (size, overflow, timeout) are configurable
via environment variables to support high-concurrency deployments.
"""

import os
import time
from functools import lru_cache
from typing import cast

import redis
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.sql.elements import TextClause
from flask import has_request_context, session


POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
if os.environ.get("USE_FAKE_REDIS") == "1":
    try:
        import fakeredis  # type: ignore
    except ImportError as exc:  # pragma: no cover - guarded import
        raise RuntimeError("USE_FAKE_REDIS=1 but fakeredis is not installed") from exc

    redis_client: redis.Redis = cast(redis.Redis, fakeredis.FakeRedis())
else:

    class _RedisProxy:
        """Lazily connect to Redis and retry a few times."""

        def __init__(self, url: str):
            self._url = url
            self._client: redis.Redis | None = None

        def _ensure(self) -> redis.Redis:
            if self._client is None:
                client = redis.Redis.from_url(self._url)
                for _ in range(5):
                    try:
                        client.ping()
                        break
                    except Exception:
                        time.sleep(0.5)
                else:
                    raise RuntimeError("Redis connection failed")
                self._client = client
            return self._client

        def __getattr__(self, name):  # pragma: no cover - thin proxy
            return getattr(self._ensure(), name)

    redis_client = cast(redis.Redis, _RedisProxy(REDIS_URL))


@lru_cache(maxsize=None)
def _get_engine(url: str | None, path: str) -> Engine:
    """Create and cache a SQLAlchemy engine for the given configuration."""

    pool_args = dict(
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT,
        pool_pre_ping=True,
        future=True,
    )
    if url:
        return create_engine(url, **pool_args)
    if path:
        return create_engine(f"sqlite:///{path}", future=True)
    raise RuntimeError(
        "DATABASE_URL or DATABASE_PATH must be configured; no default database credentials are used."
    )


class _ConnectionWrapper:
    """Bridge SQLite-style helpers with SQLAlchemy engines.

    The application still expects connections to expose ``cursor`` and
    ``execute`` methods like the built-in ``sqlite3`` connection.  By
    wrapping the raw SQLAlchemy connection we can provide those APIs while
    benefiting from SQLAlchemy's pooling and PostgreSQL support.
    """

    def __init__(self, raw, dialect):
        self._raw = raw
        self._dialect = dialect

    def cursor(self):
        return self._raw.cursor()

    def execute(self, sql, params=None):
        cur = self._raw.cursor()
        if isinstance(sql, TextClause):
            compiled = sql.compile(dialect=self._dialect)
            sql_str = str(compiled)
            if compiled.positiontup:
                ordered = [params[key] for key in compiled.positiontup]
                cur.execute(sql_str, ordered)
            else:
                cur.execute(sql_str, params or {})
        else:
            cur.execute(sql, params or ())
        return cur

    def commit(self):
        return self._raw.commit()

    def rollback(self):
        return self._raw.rollback()

    def close(self):
        return self._raw.close()


def get_db():
    """Return a DB-API connection with tenant context applied."""

    url = os.environ.get("DATABASE_URL")
    path = os.environ.get("DATABASE_PATH", "erp.db")
    engine = _get_engine(url, path)
    raw = engine.raw_connection()
    # Only attempt to set tenant context when using PostgreSQL.
    if engine.url.get_backend_name().startswith("postgres") and has_request_context():
        org_id = session.get("org_id")
        if org_id is not None:
            cur = raw.cursor()
            cur.execute("SET erp.org_id = %s", (org_id,))
            cur.close()
    return _ConnectionWrapper(raw, engine.dialect)


def get_engine() -> Engine:
    """Return a configured SQLAlchemy Engine.

    The engine is created lazily based on the current environment
    variables, mirroring the behaviour of :func:`get_db` while allowing
    callers to work with SQLAlchemy's Engine API directly.
    """

    url = os.environ.get("DATABASE_URL")
    path = os.environ.get("DATABASE_PATH", "erp.db")
    return _get_engine(url, path)


# Backwards compatible alias used by older code paths and tests
engine: Engine = get_engine()
