# migrations/env.py
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# -----------------------------------------------------------------------------
# Alembic Config object, provides access to the *.ini values
# -----------------------------------------------------------------------------
config = context.config

# Interpret the config file for Python logging.
# This sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# -----------------------------------------------------------------------------
# DB URL normalization
# Accepts SQLALCHEMY_DATABASE_URI or DATABASE_URL (Render often sets the latter)
# Ensures:
#   - postgres:// -> postgresql+psycopg2://
#   - adds sslmode=require if missing
# -----------------------------------------------------------------------------
def _coerce_db_url(url: str | None) -> str:
    if not url:
        raise RuntimeError(
            "No database URL provided. Set SQLALCHEMY_DATABASE_URI or DATABASE_URL."
        )

    # Accept Heroku/Render-style scheme
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    # Ensure psycopg2 driver is explicit
    scheme = url.split("://", 1)[0]
    if scheme == "postgresql" and "+psycopg2" not in scheme:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

    # Require SSL unless explicitly present
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"

    return url


db_url = _coerce_db_url(
    os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
)

# Inject the final URL into alembic config (used by engine_from_config below)
config.set_main_option("sqlalchemy.url", db_url)

# If you autogenerate migrations you can set target_metadata here.
# For applying existing migrations it can be None safely.
target_metadata = None


# -----------------------------------------------------------------------------
# Offline mode (generates SQL without DB connection)
# -----------------------------------------------------------------------------
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# -----------------------------------------------------------------------------
# Online mode (connects to DB and runs migrations)
# -----------------------------------------------------------------------------
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
