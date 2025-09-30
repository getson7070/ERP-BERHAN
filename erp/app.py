# erp/app.py
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

from flask import Flask, redirect, url_for
from flask_babel import Babel
from flask_caching import Cache
from flask_compress import Compress
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from jinja2 import ChoiceLoader, FileSystemLoader

from . import limiter, oauth

# IMPORTANT: import from the real module, not the shim
from .db import get_engine, ensure_schema, RedisClient

# Globals initialized here and configured inside create_app()
socketio = SocketIO(
    async_mode="threading",  # compatible with gthread workers
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)

jwt = JWTManager()
cache = Cache()
babel = Babel()
compress = Compress()


def _template_search_paths(app: Flask) -> List[Path]:
    """
    Returns a list of template search paths, covering both package-level
    templates (erp/templates) AND project-root templates (/templates).
    """
    root = Path(app.root_path).parent  # project root
    package_templates = Path(__file__).parent / "templates"  # erp/templates
    root_templates = root / "templates"
    paths: List[Path] = []
    if package_templates.is_dir():
        paths.append(package_templates)
    if root_templates.is_dir():
        paths.append(root_templates)
    # Fallback to app.template_folder if set (usually None here)
    default_folder = app.template_folder
    if default_folder:
        p = Path(default_folder)
        if p.is_dir():
            paths.append(p)
    return paths


def _static_folder(app: Flask) -> Path | None:
    """
    Choose a static folder if present (prefer project-root /static).
    """
    root = Path(app.root_path).parent
    root_static = root / "static"
    pkg_static = Path(__file__).parent / "static"
    if root_static.is_dir():
        return root_static
    if pkg_static.is_dir():
        return pkg_static
    return None


def _register_blueprints(app: Flask) -> None:
    # Import here to avoid circulars
    from .routes.auth import bp as auth_bp
    # Register your other blueprints as needed...
    app.register_blueprint(auth_bp)


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=None,  # we install a ChoiceLoader below
        static_folder=None,    # we decide static path below
        instance_relative_config=False,
    )

    # Basic config (env-driven where possible)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-not-secret"),
        JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", "dev-jwt"),
        JWT_TOKEN_LOCATION=["headers"],
        JWT_ALGORITHM="HS256",
        JWT_SECRET_ID=os.environ.get("JWT_SECRET_ID", "v1"),
        CACHE_TYPE=os.environ.get("CACHE_TYPE", "null"),  # avoids warnings if unset
        BABEL_DEFAULT_LOCALE=os.environ.get("BABEL_DEFAULT_LOCALE", "en"),
        BABEL_DEFAULT_TIMEZONE=os.environ.get("BABEL_DEFAULT_TIMEZONE", "UTC"),
        MFA_ISSUER=os.environ.get("MFA_ISSUER", "ERP"),
        WEBAUTHN_RP_ID=os.environ.get("WEBAUTHN_RP_ID", "localhost"),
        WEBAUTHN_RP_NAME=os.environ.get("WEBAUTHN_RP_NAME", "ERP App"),
        WEBAUTHN_ORIGIN=os.environ.get("WEBAUTHN_ORIGIN", "http://localhost:5000"),
        OAUTH_USERINFO_URL=os.environ.get("OAUTH_USERINFO_URL", ""),
        OAUTH_PROVIDER=os.environ.get("OAUTH_PROVIDER", "sso"),
        ACCOUNT_LOCK_SECONDS=int(os.environ.get("ACCOUNT_LOCK_SECONDS", "900")),
        LOCK_THRESHOLD=int(os.environ.get("LOCK_THRESHOLD", "5")),
        LOCK_WINDOW=int(os.environ.get("LOCK_WINDOW", "300")),
        MAX_BACKOFF=int(os.environ.get("MAX_BACKOFF", "60")),
        JWT_REVOCATION_TTL=int(os.environ.get("JWT_REVOCATION_TTL", "3600")),
    )

    # Logging
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

    # Initialize extensions
    try:
        cache.init_app(app)
    except Exception:
        app.logger.warning("Flask-Caching not fully configured; continuing.")

    compress.init_app(app)
    jwt.init_app(app)
    babel.init_app(app)
    limiter.init_app(app)
    oauth.init_app(app)

    # Configure SocketIO to use app config CORS if present
    socketio.init_app(app, cors_allowed_origins=app.config.get("CORS_ORIGINS", "*"))

    # Jinja template search paths
    search_paths = _template_search_paths(app)
    app.jinja_loader = ChoiceLoader(
        [FileSystemLoader(str(p)) for p in search_paths]
    )

    # Static folder
    static_path = _static_folder(app)
    if static_path:
        app.static_folder = str(static_path)

    # Database & Redis
    engine = get_engine()
    ensure_schema(engine)

    # Ensure Redis connectivity early (helpful for JWT/ratelimits)
    RedisClient.ensure_connection()

    # Register routes
    _register_blueprints(app)

    # Default route -> login chooser
    @app.route("/")
    def index():
        return redirect(url_for("auth.choose_login"))

    return app
