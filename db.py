from __future__ import annotations
import os

# Prefer SQLAlchemy engine, fall back to sqlite3 so imports never fail
try:
    from sqlalchemy import create_engine  # type: ignore
    _DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    _engine = create_engine(_DATABASE_URL)

    def get_engine():
        return _engine

    def get_db():
        # caller should close the connection; used in tests/fixtures
        return _engine.connect()

    def get_dialect() -> str:
        try:
            return _engine.dialect.name
        except Exception:
            return "unknown"
except Exception:
    import sqlite3  # type: ignore
    _PATH = os.getenv("SQLITE_PATH", "./app.db")

    def get_engine():
        # return the path to indicate sqlite fallback
        return _PATH

    def get_db():
        return sqlite3.connect(_PATH)

    def get_dialect() -> str:
        return "sqlite"

# Keep redis_client import available for backwards-compat
try:
    from erp.db import redis_client  # type: ignore
except Exception:
    redis_client = None  # type: ignore

__all__ = ["get_engine", "get_db", "get_dialect", "redis_client"]