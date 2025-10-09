"""
Centralized extension instances and safe init sequence.

Why this matters:
- Flask-Login injects `current_user` via a context processor on every render.
  If no loader is registered at request time, it raises and 500s.
- We register a no-op `user_loader` early so anonymous pages (e.g., /choose_login)
  never crash, even before the real User model is imported/migrated.
- Later, your real `@login_manager.user_loader` can override this stub.
"""

from __future__ import annotations
import os
from typing import Optional, Callable

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, AnonymousUserMixin
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_mail import Mail
from flask_cors import CORS
from flask_socketio import SocketIO

# ---- Instances (no app bound yet) ----
db = SQLAlchemy(session_options={"autoflush": False})
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
mail = Mail()
cors = CORS()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")  # Render eventlet workers
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

# internal flag to avoid double-binding the safety loader
__safety_loader_bound = False

def init_extensions(app: Flask) -> None:
    # Database URL: e.g., postgres on Render; fall back to local sqlite if unset
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", os.getenv("DATABASE_URL", "sqlite:///app.db"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Cache (simple backend by default; swap to Redis when you scale multiple instances)
    app.config.setdefault("CACHE_TYPE", os.getenv("CACHE_TYPE", "SimpleCache"))
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")))

    # Mail (kept inert unless configured)
    app.config.setdefault("MAIL_SERVER", os.getenv("MAIL_SERVER", "localhost"))
    app.config.setdefault("MAIL_PORT", int(os.getenv("MAIL_PORT", "25")))
    app.config.setdefault("MAIL_USE_TLS", os.getenv("MAIL_USE_TLS", "0") == "1")
    app.config.setdefault("MAIL_USERNAME", os.getenv("MAIL_USERNAME"))
    app.config.setdefault("MAIL_PASSWORD", os.getenv("MAIL_PASSWORD"))
    app.config.setdefault("MAIL_DEFAULT_SENDER", os.getenv("MAIL_DEFAULT_SENDER"))

    # Rate limiting
    app.config.setdefault("RATELIMIT_ENABLED", os.getenv("RATELIMIT_ENABLED", "1") == "1")

    # Init in dependency-safe order
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    mail.init_app(app)
    cors.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    # Keep login view optional (don’t break anonymous pages)
    login_manager.login_view = os.getenv("LOGIN_VIEW", "auth.login")

    # Anonymous user class (optional, but explicit is nice)
    class _Anon(AnonymousUserMixin):
        role = "anonymous"
    login_manager.anonymous_user = _Anon


def register_safety_login_loader() -> None:
    """
    Register a no-op user_loader so templates can always access `current_user`
    without Flask-Login raising "Missing user_loader or request_loader".
    Your real loader can later re-register and override this safely.
    """
    global __safety_loader_bound
    if __safety_loader_bound:
        return

    @login_manager.user_loader
    def _safe_loader(_user_id: str):
        # Return None → current_user becomes Anonymous; no exception is raised.
        return None

    __safety_loader_bound = True


def register_common_blueprints(app: Flask) -> None:
    # Only import here to avoid circulars during init
    from .routes.main import bp as main_bp
    app.register_blueprint(main_bp)
