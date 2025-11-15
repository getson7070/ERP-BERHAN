import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Alembic Config object, provides access to .ini values
config = context.config

# Logging configuration
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------
# Load Flask app + metadata WITHOUT running db.create_all()
# ---------------------------------------------------------

def _load_flask_app():
    """
    Import the Flask app factory from FLASK_APP (default 'erp:create_app'),
    monkey-patching db.create_all to a no-op so that Alembic migrations
    do not create tables implicitly.
    """
    flask_app_spec = os.environ.get("FLASK_APP", "erp:create_app")

    if ":" in flask_app_spec:
        module_name, factory_name = flask_app_spec.split(":", 1)
    else:
        module_name, factory_name = flask_app_spec, "create_app"

    module = __import__(module_name, fromlist=[factory_name])
    factory = getattr(module, factory_name)

    # Try to patch db.create_all -> no-op
    try:
        from erp import extensions as _ext
        if hasattr(_ext, "db") and hasattr(_ext.db, "create_all"):
            def _noop_create_all(*args, **kwargs):
                print("env.py: skipping db.create_all() during Alembic metadata load")
            _ext.db.create_all = _noop_create_all
    except Exception as exc:
        print(f"env.py: warning – could not patch db.create_all: {exc}")

    app = factory()

    # Ensure Alembic uses the same DB URL as the Flask app
    uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if uri:
        config.set_main_option("sqlalchemy.url", uri)
    else:
        # As a fallback, allow DATABASE_URL / SQLALCHEMY_DATABASE_URI from env
        env_url = os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI")
        if env_url:
            config.set_main_option("sqlalchemy.url", env_url)

    return app


def _get_target_metadata():
    app = _load_flask_app()
    with app.app_context():
        try:
            from erp.extensions import db as _db
            return _db.metadata
        except Exception:
            # Fallback: user may expose metadata elsewhere
            try:
                from erp import models
                if hasattr(models, "db"):
                    return models.db.metadata
            except Exception:
                pass
            return None


target_metadata = _get_target_metadata()

# ---------------------------------------------------------
# Offline / Online migration runners
# ---------------------------------------------------------

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
