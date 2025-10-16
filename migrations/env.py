from __future__ import annotations
from logging.config import fileConfig
import os
from alembic import context
from sqlalchemy import engine_from_config, pool
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None
def _discover_metadata():
    for spec in ("app:db","src.app:db","application:db","main:db"):
        mod, attr = spec.split(":")
        try:
            m = __import__(mod, fromlist=[attr])
            db = getattr(m, attr)
            md = getattr(db, "metadata", None)
            if md is not None:
                return md
        except Exception:
            continue
    spec = os.getenv("MIGRATIONS_METADATA_PATH")
    if spec:
        mod, attr = spec.split(":")
        m = __import__(mod, fromlist=[attr])
        return getattr(m, attr)
    return None
target_metadata = _discover_metadata()

def get_url():
    url = config.get_main_option("sqlalchemy.url")
    if url and "://":
        return url
    env_url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    if env_url: return env_url
    raise RuntimeError("No DB URL for Alembic.")

def get_engine():
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = get_url()
    stmt_ms = os.getenv("DB_STATEMENT_TIMEOUT_MS","900000")
    lock_ms = os.getenv("DB_LOCK_TIMEOUT_MS","5000")
    idle_ms = os.getenv("DB_IDLE_TX_TIMEOUT_MS", stmt_ms)
    connect_args = {"options": f"-c statement_timeout={stmt_ms} -c lock_timeout={lock_ms} -c idle_in_transaction_session_timeout={idle_ms}"}
    return engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool, connect_args=connect_args)

def run_migrations_offline():
    context.configure(url=get_url(), target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = get_engine()
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
