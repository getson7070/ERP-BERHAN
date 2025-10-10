# migrations/env.py
from __future__ import annotations
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Interpret the config file for Python logging.
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---- Create the Flask app and import metadata safely ----
# We import create_app and db here; avoid importing routes that depend on request context.
try:
    from erp import create_app  # type: ignore
    from erp.extensions import db  # type: ignore
except Exception as exc:
    raise RuntimeError(f"Alembic could not import your app or db: {exc}")

app = create_app()
with app.app_context():
    target_metadata = db.Model.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("No database URL provided. Set SQLALCHEMY_DATABASE_URI or DATABASE_URL.")
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
    connectable = engine_from_config(
        {
            "sqlalchemy.url": os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL"),
        },
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection, app.app_context():
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
