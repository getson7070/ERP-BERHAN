import os
from contextlib import contextmanager
from typing import Any, Dict, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from redis import Redis

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

redis_client: Redis = Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=False)

class DB:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn
    def execute(self, stmt, params: Optional[Dict[str, Any]] = None):
        return self._conn.execute(stmt if hasattr(stmt, "compile") else text(str(stmt)), params or {})
    def commit(self):
        self._conn.commit()
    def close(self):
        self._conn.close()

def get_db() -> DB:
    conn = engine.connect()
    return DB(conn)

# Idempotent schema bootstrap to prevent "relation does not exist" crashes.
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  user_type VARCHAR(20) NOT NULL,               -- 'employee' or 'client'
  username VARCHAR(64),                         -- phone for employees
  email VARCHAR(255) UNIQUE,
  password_hash TEXT,
  role VARCHAR(64),
  permissions TEXT,                             -- comma-separated
  org_id INTEGER,
  account_locked BOOLEAN DEFAULT FALSE,
  approved_by_ceo BOOLEAN DEFAULT FALSE,
  failed_attempts INTEGER DEFAULT 0,
  last_login TIMESTAMP,
  hire_date DATE,
  salary NUMERIC(14,2),
  tin VARCHAR(20),
  institution_name VARCHAR(255),
  address VARCHAR(255),
  phone VARCHAR(32),
  region VARCHAR(64),
  city VARCHAR(64),
  mfa_secret VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS regions_cities (
  id SERIAL PRIMARY KEY,
  region VARCHAR(64) NOT NULL,
  city VARCHAR(64) NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS regions_cities_unique ON regions_cities(region, city);

CREATE TABLE IF NOT EXISTS webauthn_credentials (
  credential_id TEXT PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  org_id INTEGER,
  public_key BYTEA NOT NULL,
  sign_count BIGINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id INTEGER,
  org_id INTEGER,
  action VARCHAR(64) NOT NULL,
  details TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""

def ensure_schema():
    with engine.begin() as conn:
        conn.exec_driver_sql(SCHEMA_SQL)
