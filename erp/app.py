# erp/app.py
from __future__ import annotations

import os
import logging
from logging import StreamHandler
from typing import Optional

from flask import Flask, redirect, url_for
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from authlib.integrations.flask_client import OAuth
from jinja2 import ChoiceLoader, FileSystemLoader

# Make these importable from erp for other modules (e.g., routes/auth.py)
cache = Cache()
jwt = JWTManager()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")
limiter = Limiter(key_func=get_remote_address, default_limits=[])
oauth = OAuth()


def _configure_logging(app: Flask) -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    app.logger.setLevel(level)
    # Gunicorn provides its own handlers; attach one for local/dev too
    if not app.logger.handlers:
        handler = StreamHandler()
        handler.setLevel(level)
        app.logger.addHandler(handler)


def _register_oauth_clients(app: Flask) -> None:
    """
    Registers an 'sso' client if the standard env settings are present.
    Safe to call even if not configured.
    """
    issuer = app.config.get("OAUTH_ISSUER")
    client_id = app.config.get("OAUTH_CLIENT_ID")
    client_secret = app.config.get("OAUTH_CLIENT_SECRET")
    well_known = app.config.get("OAUTH_WELL_KNOWN_URL")
    userinfo_url = app.config.get("OAUTH_USERINFO_URL")
    if client_id and (issuer or well_known) and userinfo_url:
        oauth.register(
            name="sso",
            client_id=client_id,
            client_secret=client_secret,
            server_metadata_url=well_known,
            client_kwargs={"scope": "openid email profile"},
        )
        app.logger.info("OAuth 'sso' client registered.")
    else:
        app.logger.info("OAuth not configured; skipping register.")


def _maybe_bootstrap_regions(app: Flask) -> None:
    """
    Ensures regions_cities exists and has basic rows.
    Uses plain SQL to avoid Alembic dependency during first boot.
    """
    try:
        from .db import get_db
        from sqlalchemy import text

        conn = get_db()
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS regions_cities (
                    region TEXT NOT NULL,
                    city   TEXT NOT NULL
                )
                """
            )
        )
        # Minimal seed to keep client_registration form working
        conn.execute(
            text(
                """
                INSERT INTO regions_cities (region, city) VALUES
                ('Addis Ababa','Addis Ababa'),
                ('Amhara','Bahir Dar'),
                ('Oromia','Adama'),
                ('SNNPR','Hawassa'),
                ('Tigray','Mekelle')
                ON CONFLICT DO NOTHING
                """
            )
        )
        conn.commit()
    except Exception as e:
        app.logger.warning("regions_cities bootstrap skipped: %s", e)


def create_app(test_config: Optional[dict] = None) -> Flask:
    # IMPORTANT: app must be created before anything touches app.jinja_loader
    app = Flask(
        __name__,
        template_folder="templates",  # erp/templates
        static_folder="static",       # erp/static (if present)
    )

    # Base config
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", os.urandom(32)),
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        WTF_CSRF_TIME_LIMIT=None,
        # JWT
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", os.urandom(32)),
        JWT_TOKEN_LOCATION=["headers"],
        JWT_COOKIE_SECURE=True,
        # MFA
        MFA_ISSUER=os.getenv("MFA_ISSUER", "ERP-BERHAN"),
        # WebAuthn
        WEBAUTHN_RP_ID=os.getenv("WEBAUTHN_RP_ID", "erp-berhan-backend.onrender.com"),
        WEBAUTHN_RP_NAME=os.getenv("WEBAUTHN_RP_NAME", "ERP-BERHAN"),
        WEBAUTHN_ORIGIN=os.getenv("WEBAUTHN_ORIGIN", "https://erp-berhan-backend.onrender.com"),
        # Flask-Caching (null cache by default)
        CACHE_TYPE=os.getenv("CACHE_TYPE", "null"),
    )
    if test_config:
        app.config.update(test_config)

    _configure_logging(app)

    # Extend template search path to also include <repo-root>/templates
    repo_root = os.path.dirname(os.path.dirname(__file__))  # .../erp/.. (repo root)
    root_templates = os.path.join(repo_root, "templates")
    if os.path.isdir(root_templates):
        app.jinja_loader = ChoiceLoader([  # type: ignore[attr-defined]
            app.jinja_loader,              # default: erp/templates
            FileSystemLoader(root_templates),
        ])
        app.logger.info("Added repo-root templates path: %s", root_templates)

    # Initialize extensions (safe to call even if minimally configured)
    try:
        cache.init_app(app)
    except Exception as e:
        app.logger.warning("Cache init skipped: %s", e)

    limiter.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)
    oauth.init_app(app)
    _register_oauth_clients(app)

    # Bootstrap critical lookup data for first boot (idempotent)
    _maybe_bootstrap_regions(app)

    # Blueprints
    from .routes.auth import auth_bp  # uses limiter, oauth exposed above
    app.register_blueprint(auth_bp)

    # If you have other blueprints like 'main', register them here
    # from .routes.main import main_bp
    # app.register_blueprint(main_bp)

    # Root → login chooser
    @app.route("/")
    def index():
        return redirect(url_for("auth.choose_login"))

    # Favicon (optional, avoids 404 spam in logs)
    @app.route("/favicon.ico")
    def favicon():
        return "", 204

    return app


# Expose objects for "from erp.app import create_app, socketio"
__all__ = ["create_app", "socketio"]
