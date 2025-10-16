from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
import os, sys
from pathlib import Path
import importlib.util

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def load_db():
    """
    Load db from erp/extensions.py by file path so we don't execute erp/__init__.py.
    """
    ext_path = BASE_DIR / "erp" / "extensions.py"
    if not ext_path.exists():
        raise RuntimeError(f"Could not find {ext_path}")
    spec = importlib.util.spec_from_file_location("erp_extensions", ext_path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    assert spec.loader is not None
    spec.loader.exec_module(mod)  # type: ignore
    if not hasattr(mod, "db"):
        raise RuntimeError("erp/extensions.py does not define a `db` object")
    return mod.db

db = load_db()
target_metadata = getattr(db, "metadata", getattr(getattr(db, "Model", object), "metadata", None))

def run_migrations_offline():
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("DATABASE_URL is not set and sqlalchemy.url is empty in alembic.ini")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    ini_section = config.get_section(config.config_ini_section) or {}
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        ini_section["sqlalchemy.url"] = env_url
    elif not ini_section.get("sqlalchemy.url"):
        raise RuntimeError("DATABASE_URL is not set and sqlalchemy.url is empty in alembic.ini")

    connectable = engine_from_config(
        ini_section, prefix="sqlalchemy.", poolclass=pool.NullPool
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
