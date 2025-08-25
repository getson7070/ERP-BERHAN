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
import redis
<<<<<<< HEAD
from functools import lru_cache
=======
import sqlite3
>>>>>>> 12080d8822c0e364cac9d5b64b9664482ab79753
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from flask import has_request_context, session

<<<<<<< HEAD
POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "5"))
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)

@lru_cache(maxsize=None)
def _get_engine(url: str | None, path: str) -> Engine:
    """Create and cache a SQLAlchemy engine for the given configuration."""

    if url:
        return create_engine(url, pool_size=POOL_SIZE, future=True)
    return create_engine(f"sqlite:///{path}", future=True)
=======
# Engine is created on demand so tests can override DATABASE_URL/DATABASE_PATH
# after import. This avoids eager PostgreSQL connections during unit tests.
engine: Engine | None = None

def _get_engine() -> Engine:
    global engine
    url = os.environ.get("DATABASE_URL")
    if not url:
        db_path = os.environ.get("DATABASE_PATH")
        if db_path:
            url = f"sqlite:///{db_path}"
        else:
            url = "postgresql://postgres:postgres@127.0.0.1:5432/erp"
    if engine is None or str(engine.url) != url:
        pool_size = int(os.environ.get("DB_POOL_SIZE", "5"))
        if url.startswith("sqlite"):
            engine = create_engine(url, future=True)
        else:
            engine = create_engine(url, pool_size=pool_size, future=True)
    return engine
>>>>>>> 12080d8822c0e364cac9d5b64b9664482ab79753

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)

def get_db():
    """Return a raw DB-API connection with tenant context applied."""
<<<<<<< HEAD
    url = os.environ.get("DATABASE_URL")
    path = os.environ.get("DATABASE_PATH", "erp.db")
    engine = _get_engine(url, path)
    conn = engine.raw_connection()
    if has_request_context():
=======
    eng = _get_engine()
    conn = eng.raw_connection()
    if eng.url.get_backend_name().startswith("sqlite"):
        conn.row_factory = sqlite3.Row
    # Only attempt to set tenant context when using PostgreSQL.
    if eng.url.get_backend_name().startswith("postgres") and has_request_context():
>>>>>>> 12080d8822c0e364cac9d5b64b9664482ab79753
        org_id = session.get("org_id")
        if org_id is not None:
            cur = conn.cursor()
            try:
                cur.execute("SET my.org_id = %s", (org_id,))
            finally:
                cur.close()
    return conn
