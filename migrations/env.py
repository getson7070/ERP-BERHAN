# migrations/env.py

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Load Alembic config and logging ------------------------------
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Resolve database URL from environment ------------------------
db_url = (
    os.getenv("SQLALCHEMY_DATABASE_URI")
    or os.getenv("DATABASE_URL")
)
if not db_url:
    raise RuntimeError(
        "No database URL provided. Set SQLALCHEMY_DATABASE_URI or DATABASE_URL."
    )

# Alembic expects a URL in the config
config.set_main_option("sqlalchemy.url", db_url)

# --- Pull model metadata for autogenerate -------------------------
# We try Flask-SQLAlchemy first (db.metadata). If that import path
# differs in your project, adjust the import below.
try:
    # Your app package
    from erp.extensions import db  # Flask-SQLAlchemy instance
    target_metadata = db.metadata
except Exception:
    # Fallback: if you use plain SQLAlchemy Base
    try:
        from erp.models import Base  # type: ignore
        target_metadata = Base.metadata
    except Exception as e:
        raise RuntimeError(
            "Alembic could not import your metadata. "
            "Make sure erp.extensions.db or erp.models.Base is importable."
        ) from e

# --- Optional tweaks ----------------------------------------------
# e.g. render_as_batch for SQLite; not needed for Postgres on Render.
# def run_migrations_in_context():
#     pass

# --- Offline mode -------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (emit SQL)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

# --- Online mode --------------------------------------------------
def run_migrations_online() -> None:
    """Run migrations with a live DB connection."""
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
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

# --- Entrypoint ---------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
