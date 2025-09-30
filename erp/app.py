# erp/app.py
from __future__ import annotations
import os
from pathlib import Path

from flask import Flask, redirect, url_for
from flask_caching import Cache
from flask_compress import Compress
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix

from erp.extensions import db as sqla_db
from erp.db import get_db, redis_client  # actual helpers live in erp/db.py

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
socketio = SocketIO(async_mode="threading", cors_allowed_origins="*")  # no eventlet

def _register_blueprints(app: Flask) -> None:
    # Import inside function to avoid import-time crashes
    from .routes.auth import bp as auth_bp
    # Register other blueprints similarly
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
    # Use Redis if configured; otherwise memory storage
    storage_uri = os.getenv("REDIS_URL")
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

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    sqla_db.init_app(app)

def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(TEMPLATES_DIR),  # repo-root/templates
        static_folder=str(STATIC_DIR),       # repo-root/static
    )

    # Secrets / proxies
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", os.urandom(32))
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    # Configure components
    _configure_security(app)
    _configure_cache(app)
    _configure_babel(app)
    _configure_jwt(app)
    _configure_sqlalchemy(app)
    _configure_rate_limits(app)

    # Blueprints
    _register_blueprints(app)

    # Default route => login chooser (adjust if you use different first page)
    @app.route("/")
    def _root():
        # if your "choose login" is in auth blueprint
        return redirect(url_for("auth.choose_login"))

    # SocketIO last
    socketio.init_app(app)

    return app