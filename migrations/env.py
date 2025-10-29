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

# Import the app and metadata
from erp import create_app  # noqa
from erp.extensions import db  # noqa

# For CLI tasks (alembic revision/upgrade), default to sqlite if nothing is set
os.environ.setdefault("SQLALCHEMY_DATABASE_URI", os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///alembic_cli.db"))

def get_app():
    return create_app()

target_metadata = db.metadata

def run_migrations_offline():
    url = os.environ.get("SQLALCHEMY_DATABASE_URI")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    app = get_app()
    with app.app_context():
        conf = config.get_section(config.config_ini_section)
        url = os.environ.get("SQLALCHEMY_DATABASE_URI") or app.config["SQLALCHEMY_DATABASE_URI"]
        conf["sqlalchemy.url"] = url
        connectable = engine_from_config(
            conf,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
                include_schemas=False,
            )
            with context.begin_transaction():
                context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
