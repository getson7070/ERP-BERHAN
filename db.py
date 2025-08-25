"""Database helpers for the ERP application.

This module was originally written for a SQLite-only setup.  The
application has since moved to PostgreSQL with SQLAlchemy, but the test
suite still patches ``DATABASE_PATH`` to point to a temporary SQLite
file.  To support both scenarios, the engine is created on demand based
on the current environment variables instead of at import time.  This
mirrors production behaviour while letting the tests supply a SQLite
path without needing a running PostgreSQL server.
"""

import os
from functools import lru_cache
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from flask import has_request_context, session


POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "5"))
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)

@lru_cache(maxsize=None)
def _get_engine(url: str | None, path: str) -> Engine:
    """Create and cache a SQLAlchemy engine for the given configuration."""

    if url:
        return create_engine(url, pool_size=POOL_SIZE, future=True)
    if path:
        return create_engine(f"sqlite:///{path}", future=True)
    return create_engine("postgresql://postgres:postgres@127.0.0.1:5432/erp", pool_size=POOL_SIZE, future=True)

def get_db():
    """Return a raw DB-API connection with tenant context applied."""

    url = os.environ.get("DATABASE_URL")
    path = os.environ.get("DATABASE_PATH", "erp.db")
    engine = _get_engine(url, path)
    conn = engine.connect()
    # Provide DB-API compatibility for legacy code expecting ``cursor()``.
    if not hasattr(conn, "cursor"):
        conn.cursor = conn.connection.cursor  # type: ignore[attr-defined]
    # Only attempt to set tenant context when using PostgreSQL.
    if engine.url.get_backend_name().startswith("postgres") and has_request_context():
        org_id = session.get("org_id")
        if org_id is not None:
            conn.execute(text("SET my.org_id = :org_id"), {"org_id": org_id})
    return conn
