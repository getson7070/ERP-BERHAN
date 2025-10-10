# migrations/env.py
from __future__ import annotations

import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from erp import create_app
from erp.extensions import db  # SQLAlchemy instance

# this is the Alembic Config object, which provides access to the values within the .ini file
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

# Build the Flask app to get the database URL & metadata
app = create_app()
with app.app_context():
    target_metadata = db.metadata
    if app.config.get("SQLALCHEMY_DATABASE_URI"):
        config.set_main_option("sqlalchemy.url", app.config["SQLALCHEMY_DATABASE_URI"])
    elif app.config.get("DATABASE_URL"):
        config.set_main_option("sqlalchemy.url", app.config["DATABASE_URL"])


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
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
