# migrations/env.py
from __future__ import annotations

import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Database URL: prefer SQLALCHEMY_DATABASE_URI, fall back to DATABASE_URL
db_url = (
    os.getenv("SQLALCHEMY_DATABASE_URI")
    or os.getenv("DATABASE_URL")
)
if not db_url:
    raise RuntimeError(
        "No database URL provided. Set SQLALCHEMY_DATABASE_URI or DATABASE_URL."
    )
config.set_main_option("sqlalchemy.url", db_url)

# --- Target metadata
# Try to import metadata with minimal side-effects. If import fails or pulls in app code,
# we fall back to None (no autogenerate).
target_metadata = None
try:
    # If you have a models module that defines `db` or `Base`, you can use it here:
    # from erp.extensions import db
    # target_metadata = db.metadata
    pass
except Exception:
    target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # safe for one-off CLI runs
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
