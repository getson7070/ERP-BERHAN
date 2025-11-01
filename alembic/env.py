# alembic/env.py
import os, sys, pathlib
from configparser import ConfigParser
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Ensure /app (repo root in container) is on sys.path so "import erp" works
ROOT = pathlib.Path(__file__).resolve().parents[1]  # -> /app
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

config = context.config

# Guarded logging: only configure if sections exist
if config.config_file_name and os.path.exists(config.config_file_name):
    _cp = ConfigParser()
    _cp.read(config.config_file_name)
    if _cp.has_section("loggers") and _cp.has_section("handlers") and _cp.has_section("formatters"):
        fileConfig(config.config_file_name)

# DB URL (env first, safe fallback second)
db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://erp:erp@db:5432/erp")
config.set_main_option("sqlalchemy.url", db_url)

# Locate metadata (prefer central SQLAlchemy() instance with .metadata)
target_metadata = None

def _discover_metadata():
    candidates = [
        ("erp.extensions", "db"),  # typical: db = SQLAlchemy()
        ("erp.db",         "db"),
        ("erp",            "db"),
    ]
    for mod, sym in candidates:
        try:
            m = __import__(mod, fromlist=[sym])
            obj = getattr(m, sym, None)
            if obj is not None and hasattr(obj, "metadata"):
                return obj.metadata
        except Exception:
            continue
    # Optional override: ALEMBIC_METADATA="your.module:BaseOrDB"
    spec = os.getenv("ALEMBIC_METADATA")
    if spec:
        mod, name = spec.split(":", 1)
        m = __import__(mod, fromlist=[name])
        obj = getattr(m, name)
        return getattr(obj, "metadata", obj)

    raise RuntimeError("Could not locate SQLAlchemy metadata. Set ALEMBIC_METADATA or expose db.metadata.")

target_metadata = _discover_metadata()

def run_migrations_offline():
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
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
