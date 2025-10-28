from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context

os.environ.setdefault("ERP_SKIP_BLUEPRINTS", "1")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from erp.extensions import db
target_metadata = db.metadata

def _guess_url_from_pg_env():
    user = os.getenv("POSTGRES_USER") or os.getenv("PGUSER") or "erp"
    pwd  = os.getenv("POSTGRES_PASSWORD") or os.getenv("PGPASSWORD") or "erp"
    host = os.getenv("POSTGRES_HOST") or os.getenv("PGHOST") or "db"
    port = os.getenv("POSTGRES_PORT") or os.getenv("PGPORT") or "5432"
    name = os.getenv("POSTGRES_DB") or os.getenv("PGDATABASE") or "erp"
    return fos.environ.get("DATABASE_URL", os.environ.get("DATABASE_URL", os.environ.get("DATABASE_URL","postgresql+psycopg://erp:erp@db:5432/erp")))

def _get_url():
    url = (
        os.getenv("DATABASE_URL")
        or os.getenv("DB_URL")
        or os.getenv("SQLALCHEMY_DATABASE_URI")
        or config.get_main_option("sqlalchemy.url")
    )
    return url.strip() if url else _guess_url_from_pg_env()

def run_migrations_offline():
    url = _get_url()
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

def run_migrations_online():
    url = _get_url()
    ini_section = config.get_section(config.config_ini_section) or {}
    ini_section["sqlalchemy.url"] = url

    connectable = engine_from_config(
        ini_section,
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



