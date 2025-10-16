from __future__ import annotations

import os
from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import create_engine
from sqlalchemy.engine import url as sa_url

# Alembic Config object
config = context.config

def _normalized_db_url() -> str:
    # Prefer env var; fall back to alembic.ini
    raw = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url", "").strip()
    if not raw:
        raise RuntimeError("DATABASE_URL is not set and sqlalchemy.url is empty in alembic.ini")
    # Normalize old postgres scheme
    if raw.startswith("postgres://"):
        raw = raw.replace("postgres://", "postgresql+psycopg2://", 1)
    return raw

DB_URL = _normalized_db_url()
# Write back so script env sees the effective URL
config.set_main_option("sqlalchemy.url", DB_URL)

# If you later add models, set target_metadata to your Base.metadata
target_metadata = None

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = DB_URL
    is_sqlite = sa_url.make_url(url).get_backend_name().startswith("sqlite")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=is_sqlite,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = DB_URL
    is_sqlite = sa_url.make_url(url).get_backend_name().startswith("sqlite")
    engine = create_engine(url, poolclass=pool.NullPool, future=True)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=is_sqlite,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
