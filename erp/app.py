# erp/app.py (clean, audited)
from __future__ import annotations
import os
from pathlib import Path
from typing import List

from flask import Flask, redirect, url_for
from flask_socketio import SocketIO
from jinja2 import ChoiceLoader, FileSystemLoader

from .extensions import db, limiter, oauth, jwt, cache, compress, csrf, babel

# Single global SocketIO instance so other modules can import `socketio` from erp.app
socketio: SocketIO = SocketIO(
    async_mode="threading",  # avoid eventlet/gevent on Py3.13
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)

def _default_config() -> dict:
    return {
        "SECRET_KEY": os.environ.get("SECRET_KEY", "change-me"),
        "SQLALCHEMY_DATABASE_URI": os.environ.get("DATABASE_URL", ""),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "RATELIMIT_STORAGE_URI": os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
        "CACHE_TYPE": os.environ.get("CACHE_TYPE", "null"),
        "JWT_SECRET_KEY": os.environ.get("JWT_SECRET_KEY", os.environ.get("SECRET_KEY", "change-me")),
        "JWT_TOKEN_LOCATION": ["headers", "cookies"],
        "JWT_COOKIE_CSRF_PROTECT": True,
        "SESSION_COOKIE_SECURE": True,
        "SESSION_COOKIE_HTTPONLY": True,
        "PREFERRED_URL_SCHEME": "https",
        "MFA_ISSUER": os.environ.get("MFA_ISSUER", "ERP-Berhan"),
        # WebAuthn
        "WEBAUTHN_RP_ID": os.environ.get("WEBAUTHN_RP_ID", "erp-berhan-backend.onrender.com"),
        "WEBAUTHN_RP_NAME": os.environ.get("WEBAUTHN_RP_NAME", "ERP Berhan"),
        "WEBAUTHN_ORIGIN": os.environ.get("WEBAUTHN_ORIGIN"),
        # OAuth (if used)
        "OAUTH_USERINFO_URL": os.environ.get("OAUTH_USERINFO_URL", ""),
        "OAUTH_PROVIDER": os.environ.get("OAUTH_PROVIDER", "sso"),
        # Account lock/backoff defaults
        "LOCK_WINDOW": 300,
        "LOCK_THRESHOLD": 5,
        "MAX_BACKOFF": 60,
        "ACCOUNT_LOCK_SECONDS": 900,
        # i18n
        "BABEL_DEFAULT_LOCALE": os.environ.get("BABEL_DEFAULT_LOCALE", "en"),
        "BABEL_DEFAULT_TIMEZONE": os.environ.get("BABEL_DEFAULT_TIMEZONE", "UTC"),
        # Auto-migrate DB on startup (set AUTO_MIGRATE=0 to disable)
        "AUTO_MIGRATE": os.environ.get("AUTO_MIGRATE", "1"),
    }

def _configure_jinja_loaders(app: Flask) -> None:
    """Search templates in both /erp/templates and repo-root /templates."""
    loaders: List[FileSystemLoader] = []
    pkg_templates = Path(__file__).with_name("templates")        # erp/templates
    project_root = Path(app.root_path).parent                    # repo root
    root_templates = project_root / "templates"                  # /templates
    loaders.append(FileSystemLoader(str(pkg_templates)))
    loaders.append(FileSystemLoader(str(root_templates)))
    extra = os.environ.get("EXTRA_TEMPLATES_DIR")
    if extra:
        loaders.append(FileSystemLoader(extra))
    app.jinja_loader = ChoiceLoader(loaders)  # type: ignore[assignment]

def _register_blueprints(app: Flask) -> None:
    from .routes.auth import bp as auth_bp
    from .routes.main import bp as main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

def _configure_oauth(app: Flask) -> None:
    oauth.register(
        "sso",
        client_id=os.environ.get("OAUTH_CLIENT_ID"),
        client_secret=os.environ.get("OAUTH_CLIENT_SECRET"),
        server_metadata_url=os.environ.get("OAUTH_DISCOVERY_URL"),
        client_kwargs={"scope": "openid email profile"},
    )

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(_default_config())

    # Initialize extensions
    db.init_app(app)
    limiter.init_app(app)
    oauth.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    compress.init_app(app)
    csrf.init_app(app)
    babel.init_app(app)
    socketio.init_app(app, message_queue=os.environ.get("SOCKETIO_MESSAGE_QUEUE"))

    _configure_jinja_loaders(app)
    _register_blueprints(app)
    _configure_oauth(app)

    @app.get("/healthz")
    def healthz():
        return "ok", 200

    @app.get("/")
    def index():
        # always start at the chooser (login gate)
        return redirect(url_for("auth.choose_login"))

    # Run Alembic migrations automatically (if configured)
    if app.config.get("AUTO_MIGRATE") in ("1", "true", "True"):
        try:
            from alembic import command
            from alembic.config import Config as AlembicConfig
            alembic_ini = Path(app.root_path).parent / "alembic.ini"
            if alembic_ini.exists():
                cfg = AlembicConfig(str(alembic_ini))
                cfg.set_main_option("sqlalchemy.url", app.config["SQLALCHEMY_DATABASE_URI"] or "")
                command.upgrade(cfg, "head")
            else:
                app.logger.warning("alembic.ini not found; skipping auto-migrate")
        except Exception as e:
            app.logger.error("Database auto-migration failed: %s", e)

    return app
