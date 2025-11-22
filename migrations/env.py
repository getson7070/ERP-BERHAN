import logging
from logging.config import fileConfig

from alembic import context

# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# ---- App / DB imports ----
# Your FLASK_APP is erp:create_app, so this should exist.
from erp import create_app  # noqa: E402
from erp.extensions import db  # noqa: E402

# Metadata for 'autogenerate'
target_metadata = db.metadata


def get_url():
    """
    Fetch DB url from alembic.ini.
    In docker, this is typically already set via env interpolation.
    """
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline():
    """
    Run migrations in 'offline' mode.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Run migrations in 'online' mode inside Flask app context.
    """
    app = create_app()
    with app.app_context():
        engine = db.engine

        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
                include_schemas=True,
                # If you ever use SQLite in dev, batch helps ALTER TABLE.
                render_as_batch=(engine.dialect.name == "sqlite"),
            )

            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
