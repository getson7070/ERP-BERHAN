from logging.config import fileConfig
from alembic import context
import os, sys

# Ensure project root is importable
sys.path.append(os.getcwd())

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import Flask-SQLAlchemy metadata
from erp.extensions import db
target_metadata = db.metadata

def get_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set for Alembic")
    return url

def run_migrations_offline():
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    from sqlalchemy import pool
    from sqlalchemy.engine import create_engine
    engine = create_engine(get_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
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


