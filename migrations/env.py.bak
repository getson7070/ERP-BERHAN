from __future__ import annotations
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load target metadata from app factory dynamically
# Support either APP_FACTORY path or default import
APP_FACTORY = os.getenv("APP_FACTORY", "app:create_app")
module_name, factory_name = APP_FACTORY.split(":")

def get_metadata():
    mod = __import__(module_name, fromlist=[factory_name])
    create_app = getattr(mod, factory_name)
    app = create_app()
    db = getattr(mod, "db", None)
    if db is None and hasattr(app, "extensions") and "sqlalchemy" in app.extensions:
        db = app.extensions["sqlalchemy"].db
    if db is None:
        raise RuntimeError("Could not locate SQLAlchemy metadata via app factory")
    return db.metadata

target_metadata = get_metadata()

# Optional DB timeouts
STATEMENT_TIMEOUT = os.getenv("DB_STATEMENT_TIMEOUT_MS", "900000")  # 15min
LOCK_TIMEOUT = os.getenv("DB_LOCK_TIMEOUT_MS", "5000")
IDLE_TX_TIMEOUT = os.getenv("DB_IDLE_IN_TX_SESSION_TIMEOUT_MS", "0")

def _set_timeouts(connection):
    try:
        connection.execute(f"SET statement_timeout TO {int(STATEMENT_TIMEOUT)}")
        connection.execute(f"SET lock_timeout TO {int(LOCK_TIMEOUT)}")
        if int(IDLE_TX_TIMEOUT) > 0:
            connection.execute(f"SET idle_in_transaction_session_timeout = {int(IDLE_TX_TIMEOUT)}")
    except Exception:
        # don't hard-fail alembic for timeouts
        pass

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,
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
        _set_timeouts(connection)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
