import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your app/db to expose metadata
from erp.app import create_app
from erp.extensions import db

app = create_app()
target_metadata = db.metadata

def _db_url():
    url = os.getenv("DATABASE_URL")
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url or config.get_main_option("sqlalchemy.url")

def run_migrations_offline():
    context.configure(
        url=_db_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    ini_section = config.get_section(config.config_ini_section)
    ini_section["sqlalchemy.url"] = _db_url()
    connectable = engine_from_config(
        ini_section, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
