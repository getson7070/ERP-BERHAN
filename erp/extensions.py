from __future__ import annotations
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, AnonymousUserMixin
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
cache = Cache(config={"CACHE_TYPE": "SimpleCache"})
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

class _Anon(AnonymousUserMixin):
    name = "Guest"
    email = None
    @property
    def is_admin(self): return False
    @property
    def roles(self): return []

def init_extensions(app: Flask) -> None:
    # Security & defaults
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("SESSION_COOKIE_SECURE", True)
    app.config.setdefault("PREFERRED_URL_SCHEME", "https")
    app.config.setdefault("RATELIMIT_ENABLED", True)

    CORS(app, resources={r"*": {"origins": "*"}})

    # Redis queue (optional)
    redis_url = os.getenv("REDIS_URL") or os.getenv("RATELIMIT_STORAGE_URI")
    if redis_url:
        app.config["SOCKETIO_MESSAGE_QUEUE"] = redis_url

    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app)

    # Login manager setup (prevents 'Missing user_loader' crash)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # adjust if your route differs
    login_manager.anonymous_user = _Anon  # type: ignore

    # Defer to canonical user_loader if present; else safe fallback
    try:
        from .auth.user_loader import register_user_loader  # type: ignore
        register_user_loader(login_manager)
    except Exception:
        @login_manager.user_loader
        def _default_user_loader(user_id: str):
            # Safe fallback: no user lookup; anonymous session works without crashing
            return None

def register_blueprints(app: Flask) -> None:
    # Import inside function to avoid import-time side effects
    from .routes.main import bp as main_bp
    from .routes.auth import auth_bp
    from .routes.api import api_bp
    try:
        from .routes.health import health_bp
        app.register_blueprint(health_bp)
    except Exception:
        pass

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp)
