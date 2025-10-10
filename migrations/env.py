# migrations/env.py
from __future__ import annotations
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# this Alembic Config object provides access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# If you have metadata for autogenerate, import it here, e.g.:
# from erp.models import Base
# target_metadata = Base.metadata
target_metadata = None  # static migrations work without metadata

def _load_url() -> str | None:
    url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url

def run_migrations_offline():
    url = _load_url()
    if not url:
        raise RuntimeError("DATABASE_URL (or sqlalchemy.url) must be set for offline migrations")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    section = config.get_section(config.config_ini_section) or {}
    url = _load_url()
    if not url:
        raise RuntimeError("DATABASE_URL (or sqlalchemy.url) must be set for online migrations")
    section["sqlalchemy.url"] = url

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
