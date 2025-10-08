# erp/extensions.py
from __future__ import annotations

import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

# Do NOT pass default_limits to init_app() on v3.x – use config instead.
limiter = Limiter(key_func=get_remote_address, enabled=True)

# SocketIO: eventlet is used in production
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")


def _apply_default_config(app):
    # DATABASE
    uri = (
        app.config.get("SQLALCHEMY_DATABASE_URI")
        or os.getenv("SQLALCHEMY_DATABASE_URI")
        or os.getenv("DATABASE_URL")
    )
    if uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Cache
    app.config.setdefault("CACHE_TYPE", os.getenv("CACHE_TYPE", "SimpleCache"))
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")))

    # Rate limiting (Flask-Limiter 3.x)
    # strings or list of strings are fine; avoid stringified lists.
    app.config.setdefault("RATELIMIT_DEFAULTS", ["300 per minute", "30 per second"])
    app.config.setdefault("RATELIMIT_ENABLED", True)
    app.config.setdefault("RATELIMIT_STORAGE_URI", os.getenv("RATELIMIT_STORAGE_URI", "memory://"))

    # CSRF + Secret
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "dev-secret-change-me"))

    # SocketIO message queue (optional: Redis)
    mq = os.getenv("SOCKETIO_MESSAGE_QUEUE")
    if mq:
        app.config["SOCKETIO_MESSAGE_QUEUE"] = mq


def init_extensions(app):
    _apply_default_config(app)

    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    csrf.init_app(app)

    # Login manager
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Provide a user_loader so Flask-Login stops throwing during template render.
    @login_manager.user_loader
    def load_user(user_id: str):
        # Import lazily to avoid circulars
        try:
            from erp.models import User  # type: ignore
        except Exception:  # models may be named differently – fail soft
            return None
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # Limiter (v3.x): configured through app.config
    limiter.init_app(app)

    # Mail
    mail.init_app(app)

    # SocketIO
    socketio.init_app(
        app,
        message_queue=app.config.get("SOCKETIO_MESSAGE_QUEUE"),
        cors_allowed_origins="*",
    )
