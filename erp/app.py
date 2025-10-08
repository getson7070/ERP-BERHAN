# erp/app.py
from __future__ import annotations

import os
import secrets
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf import CSRFProtect
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

# --- Extension singletons (imported elsewhere without creating cycles) ---
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
cache = Cache()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

# Limiter is optional; safe default is in-memory so it won't require Redis.
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"], storage_uri="memory://")


def _database_uri_from_env() -> str:
    uri = os.environ.get("DATABASE_URL", "").strip()
    if not uri:
        # Fallback for local dev or first boot; Alembic still works with SQLite.
        return "sqlite:///app.db"
    # Render sometimes provides `postgres://` which SQLAlchemy 2.x rejects.
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    return uri


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # --- Core config ---
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    app.config["SQLALCHEMY_DATABASE_URI"] = _database_uri_from_env()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Sessions / security (good defaults for Render)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("SESSION_COOKIE_SECURE", True)  # Render serves over https
    app.config.setdefault("PREFERRED_URL_SCHEME", "https")

    # Flask-Caching: simple in-process cache by default
    app.config.setdefault("CACHE_TYPE", "SimpleCache")
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", 300)

    # If you have REDIS_URL, use it for SocketIO and Limiter automatically
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        # socketio can share Redis for pub/sub if you scale workers
        app.config["SOCKETIO_MESSAGE_QUEUE"] = redis_url
        limiter._storage_uri = redis_url  # switch rate limit storage to Redis

    # --- Init extensions (order matters a bit) ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # SocketIO wraps the app for websocket endpoints (WSGI still works with Gunicorn eventlet worker)
    socketio.init_app(app)

    # CORS: allow your frontend(s). Use CORS_ORIGINS env (comma-sep) or "*"
    origins = os.environ.get("CORS_ORIGINS", "*")
    CORS(app, resources={r"/*": {"origins": [o.strip() for o in origins.split(",")]}})

    # --- Blueprints (import inside function to avoid circular imports) ---
    from erp.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    # auth blueprint is optional but likely present in your project
    try:
        from erp.routes.auth import bp as auth_bp
        app.register_blueprint(auth_bp, url_prefix="/auth")
    except Exception:
        # Keep app booting even if auth module isn’t ready during early migrations
        pass

    # LoginManager defaults
    login_manager.login_view = "auth.login"  # endpoint name inside the auth blueprint, if present

    # Simple ping route for health checks (also exposed in main blueprint as /healthz if you kept it)
    @app.get("/_health")
    def _health():
        return {"status": "ok"}, 200

    return app
