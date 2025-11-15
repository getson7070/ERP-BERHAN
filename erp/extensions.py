"""
erp.extensions
Central place for Flask extension instances and their initialization.

This module is imported very early by erp.__init__, Alembic env.py, and
other modules, so avoid heavy side effects at import time.
"""

from __future__ import annotations

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- Core extensions ---------------------------------------------------------

db: SQLAlchemy = SQLAlchemy()
migrate: Migrate = Migrate()

cache: Cache = Cache()
mail: Mail = Mail()

limiter: Limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],  # Configure per-view or via app.config if needed
)

login_manager: LoginManager = LoginManager()

# --- Flask-Login configuration & loader -------------------------------------


@login_manager.user_loader
def load_user(user_id: str):
    """
    Flask-Login callback: given a user_id stored in the session, return
    the corresponding User instance or None.

    user_id is stored as a string in the session; our User.id is integer.
    """
    # Import inside function to avoid circular imports during app startup
    from erp.models.user import User

    if not user_id:
        return None
    try:
        return User.query.get(int(user_id))
    except (TypeError, ValueError):
        # Malformed or non-integer user_id in session
        return None


# --- Extension init hook -----------------------------------------------------


def init_extensions(app: Flask) -> None:
    """
    Initialize all Flask extensions with the given app instance.

    This is called from erp.create_app() and must remain idempotent.
    """
    # Database + migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # Caching and mail (safe even if not heavily used yet)
    cache.init_app(app)
    mail.init_app(app)

    # Rate limiting (backed by Redis via app.config or default)
    limiter.init_app(app)

    # Login manager
    login_manager.init_app(app)
    # Ensure this matches your blueprint endpoint for the login page
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    # Optional: allow anonymous users by default (Flask-Login default),
    # but you could override login_manager.anonymous_user if needed.
