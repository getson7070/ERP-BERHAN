import os
import logging
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
import redis as _redis


# ---- SQLAlchemy engine -------------------------------------------------------

_ENGINE: Optional[Engine] = None

def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    # Render sometimes provides postgres URL without sslmode; explicit is safer
    if "sslmode=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url

def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine(_database_url(), pool_pre_ping=True, future=True)
    return _ENGINE


@contextmanager
def get_db() -> Connection:
    """Context manager returning a SQLAlchemy Connection with commit/close."""
    engine = get_engine()
    with engine.connect() as conn:
        yield conn


# ---- Schema bootstrap --------------------------------------------------------

def ensure_schema(engine: Engine) -> None:
    """
    Create the minimal tables used by erp.routes.auth if they don't exist.
    Non-destructive: uses CREATE TABLE IF NOT EXISTS.
    """
    with engine.begin() as conn:
        # users
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
          id SERIAL PRIMARY KEY,
          user_type TEXT NOT NULL,          -- 'employee' | 'client'
          username TEXT UNIQUE,
          email TEXT UNIQUE,
          password_hash TEXT,
          role TEXT,
          permissions TEXT,
          hire_date DATE,
          salary NUMERIC,
          tin TEXT,
          institution_name TEXT,
          address TEXT,
          phone TEXT,
          region TEXT,
          city TEXT,
          approved_by_ceo BOOLEAN DEFAULT FALSE,
          failed_attempts INTEGER DEFAULT 0,
          account_locked BOOLEAN DEFAULT FALSE,
          last_login TIMESTAMP,
          mfa_secret TEXT,
          org_id INTEGER
        );
        """))

        # regions_cities
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS regions_cities (
          region TEXT NOT NULL,
          city   TEXT NOT NULL
        );
        """))

        # webauthn_credentials
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS webauthn_credentials (
          credential_id TEXT PRIMARY KEY,
          user_id INTEGER NOT NULL,
          org_id INTEGER,
          public_key BYTEA,
          sign_count INTEGER DEFAULT 0
        );
        """))

        # Seed at least one region/city to avoid empty dropdowns
        conn.execute(text("""
        INSERT INTO regions_cities (region, city)
        SELECT 'Addis Ababa', 'Addis Ababa'
        WHERE NOT EXISTS (SELECT 1 FROM regions_cities);
        """))


# ---- Redis client (rate limiting, login backoff, token storage) --------------

class RedisClient:
    client: Optional[_redis.Redis] = None

    @classmethod
    def ensure_connection(cls, app=None) -> Optional[_redis.Redis]:
        if cls.client:
            return cls.client
        url = os.environ.get("REDIS_URL")
        if not url:
            if app:
                app.logger.warning("REDIS_URL not set; using in-memory fallback for dev.")
            return None
        try:
            cls.client = _redis.from_url(url, decode_responses=False)
            # liveness check
            cls.client.ping()
            return cls.client
        except Exception as e:
            if app:
                app.logger.warning("Redis connection failed: %s", e)
            return None

# Backward-compat alias expected by your code
redis_client = RedisClient.ensure_connection()
