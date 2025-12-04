"""Alembic environment configuration for ERP-BERHAN.

This file wires Alembic to the real Flask application so that migrations
run against the same SQLAlchemy configuration the app uses.
"""

from __future__ import annotations

import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

# ----------------------------------------------------------------------
# Import the Flask app + SQLAlchemy extension
# ----------------------------------------------------------------------
from erp import create_app

# Create the Flask application using the factory pattern
app = create_app()

# Get SQLAlchemy instance from the Flask app
ext = app.extensions.get("sqlalchemy")
if isinstance(ext, dict) and "db" in ext:
    db = ext["db"]
else:
    db = getattr(ext, "db", ext)

# Ensure ALL models are imported so metadata is complete
# (models live in erp/models/*.py)
import erp.models  # noqa: F401

# Provide Alembic with the metadata from SQLAlchemy
target_metadata = db.Model.metadata

# Interpret the Alembic config
config = context.config

# Configure Python logging from alembic.ini if present
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")


def get_url() -> str:
    """Return the DB URL from the Flask app config.

    This keeps Alembic aligned with the application's DATABASE_URL /
    SQLALCHEMY_DATABASE_URI resolution logic.
    """
    return str(app.config["SQLALCHEMY_DATABASE_URI"])


# ----------------------------------------------------------------------
# Run migrations offline
# ----------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations without a DB connection."""

    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,           # Detect column type changes
        compare_server_default=True, # Detect server default changes
    )

    with context.begin_transaction():
        context.run_migrations()


# ----------------------------------------------------------------------
# Run migrations online (normal mode)
# ----------------------------------------------------------------------
def run_migrations_online() -> None:
    """Run migrations with a real DB connection.

    IMPORTANT:
    We must push a Flask application context so that Flask-SQLAlchemy’s
    `db.engine` can be accessed without triggering the "working outside
    of application context" RuntimeError.
    """

    # All Flask / db access must happen inside app.app_context()
    with app.app_context():
        connectable = db.engine

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,              # Detect schema drift
                compare_server_default=True,    # Detect server default changes
                render_as_batch=True,           # Safe for SQLite + Postgres
                include_schemas=True,
            )

            with context.begin_transaction():
                context.run_migrations()


# ----------------------------------------------------------------------
# Entrypoint Alembic will call
# ----------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
