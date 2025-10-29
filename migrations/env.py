from __future__ import annotations
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config  # do NOT call fileConfig; avoid logging dependency

from erp import create_app  # noqa
from erp.extensions import db  # noqa

# default SQLite for CLI tasks if nothing provided
os.environ.setdefault(
    "SQLALCHEMY_DATABASE_URI",
    os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///alembic_cli.db"),
)
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
    app = create_app()
    with app.app_context():
        conf = config.get_section(config.config_ini_section) or {}
        url = os.environ.get("SQLALCHEMY_DATABASE_URI") or app.config["SQLALCHEMY_DATABASE_URI"]
        conf["sqlalchemy.url"] = url
        connectable = engine_from_config(conf, prefix="sqlalchemy.", poolclass=pool.NullPool)
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
