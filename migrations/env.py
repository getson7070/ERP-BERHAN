from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Alembic Config object
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _db_url() -> str:
    url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    if not url:
        raise RuntimeError("Missing DATABASE_URL (or SQLALCHEMY_DATABASE_URI). Cannot run migrations.")
    # Render often uses postgres:// which SQLAlchemy expects as postgresql://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


def _safe_url(url: str) -> str:
    # hide password in logs
    try:
        prefix, rest = url.split("://", 1)
        if "@" in rest and ":" in rest.split("@")[0]:
            userpass, hostpart = rest.split("@", 1)
            user = userpass.split(":", 1)[0]
            return f"{prefix}://{user}:***@{hostpart}"
    except Exception:
        pass
    return "***"


# If you have metadata, you can set it; otherwise keep None (we use revision scripts)
target_metadata = None


def run_migrations_offline() -> None:
    url = _db_url()
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
    url = _db_url()

    # Force alembic to use the runtime URL, not alembic.ini sqlalchemy.url
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = url

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    print(f"[alembic.env] Using DB URL: {_safe_url(url)}")

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
