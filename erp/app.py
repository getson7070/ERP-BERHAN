# erp/app.py
from __future__ import annotations
import os
from pathlib import Path
from flask import Flask
from flask_caching import Cache
from flask_compress import Compress
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_babel import Babel
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Local
from .extensions import db as sqla_db  # if you have a flask_sqlalchemy 'db' instance
from . import models  # ensure models are imported for Alembic autogenerate use-cases
from erp.db import get_db, redis_client  # current repo's shim/real implementations

# Resolve template/static at REPO ROOT (not inside erp/)
PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
STATIC_DIR = REPO_ROOT / "static"

cache = Cache()
compress = Compress()
csrf = CSRFProtect()
babel = Babel()
jwt = JWTManager()

# IMPORTANT: do NOT use eventlet in Python 3.13; use threading
socketio = SocketIO(async_mode="threading", cors_allowed_origins="*")  # adjust CORS per your needs

def _register_blueprints(app: Flask) -> None:
    # Import locally to avoid circulars
    from .routes.auth import bp as auth_bp
    from .routes.admin import bp as admin_bp
    from .routes.api import bp as api_bp
    # add other blueprints here

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

def _configure_security(app: Flask) -> None:
    # Basic hardening defaults; override via env in Render
    app.config.setdefault("SESSION_COOKIE_SECURE", True)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("WTF_CSRF_ENABLED", True)
    app.config.setdefault("PREFERRED_URL_SCHEME", "https")

def _configure_cache(app: Flask) -> None:
    # Works even if CACHE_TYPE not set; harmless warning if left null
    cache.init_app(app)
    compress.init_app(app)

def _configure_babel(app: Flask) -> None:
    babel.init_app(app)

def _configure_jwt(app: Flask) -> None:
    jwt.init_app(app)

def _configure_rate_limits(app: Flask) -> None:
    # Prefer Redis if available; otherwise fall back to in-memory (warning in logs)
    storage_uri = None
    if redis_client.is_real:
        storage_uri = app.config.get("REDIS_URL") or os.getenv("REDIS_URL")
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=storage_uri or "memory://",
        strategy="fixed-window",
    )
    limiter.init_app(app)
    app.extensions["limiter"] = limiter  # if you need it later

def _configure_sqlalchemy(app: Flask) -> None:
    # This repo uses Flask-SQLAlchemy for models, but also exposes a raw session in erp.db
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    sqla_db.init_app(app)

def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(TEMPLATES_DIR),
        static_folder=str(STATIC_DIR),
    )

    # Mandatory secrets
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", os.urandom(32))

    # Respect reverse proxy (Render)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    _configure_security(app)
    _configure_cache(app)
    _configure_babel(app)
    _configure_jwt(app)
    _configure_sqlalchemy(app)
    _configure_rate_limits(app)

    # Blueprints last (after extensions)
    _register_blueprints(app)

    # Attach SocketIO AFTER app created
    socketio.init_app(app)

    return app
