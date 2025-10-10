# migrations/env.py
from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ----------------------------------------------------------------------
# Load Flask app and metadata safely (Flask-SQLAlchemy -> db.metadata)
# ----------------------------------------------------------------------
# Prefer SQLALCHEMY_DATABASE_URI; fall back to DATABASE_URL
database_url = (
    os.getenv("SQLALCHEMY_DATABASE_URI")
    or os.getenv("DATABASE_URL")
)

if not database_url:
    raise RuntimeError(
        "No database URL provided. Set SQLALCHEMY_DATABASE_URI or DATABASE_URL."
    )

# Make sure Alembic knows the URL
config.set_main_option("sqlalchemy.url", database_url)

# Import the Flask app factory and db lazily
try:
    from erp import create_app  # type: ignore
    from erp.extensions import db  # type: ignore
except Exception as exc:
    raise RuntimeError(
        f"Alembic could not import your app or db: {exc}"
    )

# Create the app and push an app context so db.metadata is available
app = create_app()
app.app_context().push()

target_metadata = db.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
