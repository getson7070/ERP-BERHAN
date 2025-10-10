# migrations/env.py
from __future__ import annotations

import os
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy.engine import Engine
from alembic import context

# ---------------------------------------------------------
# We do NOT import your Flask app or routes here.
# We keep migrations independent of app imports.
# ---------------------------------------------------------

config = context.config

# Build the DB URL from env. Prefer SQLALCHEMY_DATABASE_URI, else DATABASE_URL
db_url = (
    os.environ.get("SQLALCHEMY_DATABASE_URI")
    or os.environ.get("DATABASE_URL")
)
if not db_url:
    raise RuntimeError("No database URL provided. Set SQLALCHEMY_DATABASE_URI or DATABASE_URL.")

# Inject URL into Alembic config (so script location etc. still works)
config.set_main_option("sqlalchemy.url", db_url)

# If you ever need model metadata for autogenerate, import and set it here.
# For now, set to None (we're using explicit SQL in versions).
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
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode'."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=db_url,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
