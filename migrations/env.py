# migrations/env.py
from __future__ import annotations

import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def _coerce_db_url(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    scheme = url.split("://", 1)[0]
    if scheme == "postgresql" and "+psycopg2" not in scheme:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url

db_url = (
    os.getenv("SQLALCHEMY_DATABASE_URI")
    or os.getenv("DATABASE_URL")
)

db_url = _coerce_db_url(db_url)
if not db_url:
    raise RuntimeError("No database URL provided. Set SQLALCHEMY_DATABASE_URI or DATABASE_URL.")

config.set_main_option("sqlalchemy.url", db_url)

target_metadata = None  # import your models' metadata if using autogenerate

def run_migrations_offline():
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
