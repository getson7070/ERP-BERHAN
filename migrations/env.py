import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Alembic Config
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add project root to import path (so `erp` can be imported)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import metadata from your app
from erp.extensions import db  # type: ignore

target_metadata = db.metadata

def _normalize_url(url: str) -> str:
    url = (url or "").strip()
    if url.startswith("postgres://"):
        # Normalize deprecated scheme to SQLAlchemy's expected driver syntax
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url

def get_url() -> str:
    env_url = _normalize_url(os.getenv("DATABASE_URL", ""))
    if env_url:
        return env_url
    # fallback to alembic.ini if present
    ini_url = _normalize_url(config.get_main_option("sqlalchemy.url") or "")
    return ini_url or "sqlite:///dev.db"

def run_migrations_offline() -> None:
    \"\"\"Run migrations in 'offline' mode.\"\"\"
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={\"paramstyle\": \"named\"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    \"\"\"Run migrations in 'online' mode.\"\"\"
    ini_section = config.get_section(config.config_ini_section) or {}
    ini_section[\"sqlalchemy.url\"] = get_url()

    connectable = engine_from_config(
        ini_section,
        prefix=\"sqlalchemy.\",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=(connection.dialect.name == \"sqlite\"),
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
