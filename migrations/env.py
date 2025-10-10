# migrations/env.py
from __future__ import with_statement

from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool  # noqa: F401  (kept for completeness)
from flask import current_app

# Interpret the config file for Python logging.
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Build the Flask app and load metadata ---
from erp import create_app
from erp.extensions import db

app = create_app()

with app.app_context():
    target_metadata = db.metadata

    def run_migrations_offline():
        """Run migrations in 'offline' mode."""
        url = current_app.config.get("SQLALCHEMY_DATABASE_URI")
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
        """Run migrations in 'online' mode."""
        connectable = db.engine
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
