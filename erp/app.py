# erp/app.py
from __future__ import annotations
import os
from pathlib import Path

from flask import Flask
from flask_caching import Cache
from flask_compress import Compress
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix

from .extensions import db as sqla_db  # your Flask-SQLAlchemy() instance, if present
from . import models  # ensure models import for Alembic autogenerate, if needed
from erp.db import get_db, redis_client  # your real implementations

# Resolve repo-root templates/static (your repo stores them at top level)
PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
STATIC_DIR = REPO_ROOT / "static"

cache = Cache()
compress = Compress()
csrf = CSRFProtect()
babel = Babel()
jwt = JWTManager()

# Do NOT use eventlet with Python 3.13
socketio = SocketIO(async_mode="threading", cors_allowed_origins="*")  # tighten CORS as needed

def _register_blueprints(app: Flask) -> None:
    from .routes.auth import bp as auth_bp
    # register all other blueprints here
    app.register_blueprint(auth_bp)

def _configure_security(app: Flask) -> None:
    app.config.setdefault("SESSION_COOKIE_SECURE", True)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("WTF_CSRF_ENABLED", True)
    app.config.setdefault("PREFERRED_URL_SCHEME", "https")

def _configure_cache(app: Flask) -> None:
    cache.init_app(app)
    compress.init_app(app)

def _configure_babel(app: Flask) -> None:
    babel.init_app(app)

def _configure_jwt(app: Flask) -> None:
    jwt.init_app(app)

def _configure_rate_limits(app: Flask) -> None:
    # Use Redis if configured; otherwise memory storage (warns in logs but doesn’t crash)
    storage_uri = None
    if redis_client.is_real:
        storage_uri = app.config.get("REDIS_URL") or os.getenv("REDIS_URL")

    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=storage_uri or "memory://",
        strategy="fixed-window",
    )
    limiter.init_app(app)
    app.extensions["limiter"] = limiter

def _configure_sqlalchemy(app: Flask) -> None:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    # SQLAlchemy 2.x
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    sqla_db.init_app(app)

def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(TEMPLATES_DIR),
        static_folder=str(STATIC_DIR),
    )

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", os.urandom(32))
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    _configure_security(app)
    _configure_cache(app)
    _configure_babel(app)
    _configure_jwt(app)
    _configure_sqlalchemy(app)
    _configure_rate_limits(app)

    _register_blueprints(app)
    socketio.init_app(app)

    return app