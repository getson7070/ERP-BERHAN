"""Central registry for Flask extension singletons.

The project imports this module in a variety of contexts (Flask app
factory, Alembic, tests), so construction of the extension instances must
remain lightweight and free of side effects.
"""

from __future__ import annotations

import importlib.util
import os

from flask import Flask
from flask_caching import Cache
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

if importlib.util.find_spec("flask_limiter") is not None:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
else:  # pragma: no cover - fallback when Flask-Limiter is optional
    class Limiter:  # type: ignore
        def __init__(self, *_, **__):
            self.enabled = False

        def init_app(self, app: Flask) -> None:
            app.logger.warning(
                "Flask-Limiter is not installed; rate limiting is disabled"
            )

        def limit(self, *_args, **_kwargs):  # noqa: D401 - mimic real decorator
            def decorator(fn):
                return fn

            return decorator

    def get_remote_address():  # type: ignore
        return "127.0.0.1"

if importlib.util.find_spec("flask_mail") is not None:
    from flask_mail import Mail
else:  # pragma: no cover - fallback when Flask-Mail is optional
    class Mail:  # type: ignore
        def init_app(self, app: Flask) -> None:  # noqa: D401
            app.logger.warning(
                "Flask-Mail is not installed; email delivery features are disabled"
            )

if importlib.util.find_spec("flask_wtf") is not None:
    from flask_wtf.csrf import CSRFProtect
else:  # pragma: no cover - fallback when Flask-WTF is optional
    class CSRFProtect:  # type: ignore
        def init_app(self, app: Flask) -> None:  # noqa: D401
            app.logger.warning(
                "Flask-WTF is not installed; CSRF protection is disabled",
            )

_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# --- Core extensions ---------------------------------------------------------

db: SQLAlchemy = SQLAlchemy(metadata=MetaData(naming_convention=_NAMING_CONVENTION))
migrate: Migrate = Migrate()

cache: Cache = Cache()
mail: Mail = Mail()
csrf: CSRFProtect = CSRFProtect()

limiter: Limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],  # Configure per-view or via app.config if needed
    storage_uri=(
        os.environ.get("RATELIMIT_STORAGE_URI")
        or os.environ.get("REDIS_URL")
        or "memory://"
    ),
)

login_manager: LoginManager = LoginManager()

# --- Flask-Login configuration & loader -------------------------------------


@login_manager.user_loader
def load_user(user_id: str):
    """
    Flask-Login callback for *all* principals (employees + clients).

    The loader performs basic integrity checks so inactive or unverified
    principals are not restored into an authenticated session, ensuring a
    single policy enforcement point for identity resolution.
    """

    # Import inside function to avoid circular imports during app startup
    from erp.models.user import User
    from erp.models.client_auth import ClientAccount

    if not user_id:
        return None

    if isinstance(user_id, str) and user_id.startswith("client:"):
        try:
            client_id = int(user_id.split(":", 1)[1])
        except (TypeError, ValueError, IndexError):
            return None

        client: ClientAccount | None = ClientAccount.query.get(client_id)
        if client is None:
            return None
        if not getattr(client, "is_active", True):
            return None
        if not getattr(client, "is_verified", False):
            # Enforce approval/verification gate for client principals
            return None
        return client

    try:
        employee = User.query.get(int(user_id))
    except (TypeError, ValueError):
        # Malformed or non-integer user_id in session
        return None

    if employee is None:
        return None
    if not getattr(employee, "is_active", True):
        return None

    return employee


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
    csrf.init_app(app)

    # Rate limiting (backed by Redis via app.config or default)
    limiter.init_app(app)

    # Login manager
    login_manager.init_app(app)
    # Ensure this matches your blueprint endpoint for the login page
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    # Optional: allow anonymous users by default (Flask-Login default),
    # but you could override login_manager.anonymous_user if needed.
