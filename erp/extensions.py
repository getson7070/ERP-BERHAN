from __future__ import annotations

import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
mail = Mail()
login_manager = LoginManager()

# we rebind this in init_extensions so we can pass config-driven defaults
limiter: Limiter | None = None

# Socket.IO – eventlet worker on Render
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")


def init_extensions(app):
    """
    Initialize all extensions with app config.
    - Properly configures Flask-Limiter 3.x with default limits
    - Registers a safe flask-login user_loader
    """
    cache.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # ---- Flask-Login user loader (safe and optional) -----------------------
    @login_manager.user_loader
    def load_user(user_id: str):
        # Try a couple of common model import paths gracefully.
        try:
            from .models.user import User  # type: ignore
        except Exception:
            try:
                from .models import User  # type: ignore
            except Exception:
                User = None  # type: ignore
        if not user_id or not User:
            return None
        try:
            # SQLAlchemy 2.x: session.get(Model, pk)
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # ---- Flask-Limiter 3.x -------------------------------------------------
    default_limits = app.config.get("RATELIMIT_DEFAULT", None)  # None | str | list[str]
    storage_uri = app.config.get("RATELIMIT_STORAGE_URI", "memory://")

    # Recreate the limiter with proper defaults so .init_app accepts it
    global limiter
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=storage_uri,
        default_limits=default_limits if default_limits else None,
    )
    limiter.init_app(app)

    # ---- Socket.IO ---------------------------------------------------------
    socketio.init_app(app)
