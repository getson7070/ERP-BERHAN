# migrations/env.py
from __future__ import annotations
from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool
from alembic import context

# Use your Flask app's metadata
from erp.app import create_app
from erp.extensions import db

config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Build app to access models/metadata
app = create_app()
target_metadata = db.metadata

# Prefer env DATABASE_URL; fall back to SQLALCHEMY_DATABASE_URI
db_url = (
    os.getenv("DATABASE_URL")
    or os.getenv("SQLALCHEMY_DATABASE_URI")
    or app.config.get("SQLALCHEMY_DATABASE_URI")
)

def run_migrations_offline():
    url = db_url
    if not url:
        raise SystemExit("DATABASE_URL/SQLALCHEMY_DATABASE_URI not set for offline migrations.")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    if not db_url:
        raise SystemExit("DATABASE_URL/SQLALCHEMY_DATABASE_URI not set for online migrations.")

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = db_url

    connectable = engine_from_config(
        configuration,
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
