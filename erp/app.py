# erp/app.py
# at the top with other imports
from flask_socketio import SocketIO

# ...
# replace the previous socketio init line with eventlet mode:
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

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

cache = Cache()
jwt = JWTManager()
# IMPORTANT: move away from eventlet → gevent
socketio = SocketIO(async_mode="gevent", cors_allowed_origins="*")
limiter = Limiter(key_func=get_remote_address, default_limits=[])
oauth = OAuth()


def _configure_logging(app: Flask) -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    app.logger.setLevel(level)
    if not app.logger.handlers:
        handler = StreamHandler()
        handler.setLevel(level)
        app.logger.addHandler(handler)


def _register_oauth_clients(app: Flask) -> None:
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


def _maybe_bootstrap_core_tables_and_admin(app: Flask) -> None:
    """
    Ensure 'users' and 'webauthn_credentials' exist.
    If 'users' is empty, create a first admin using env:
      ADMIN_EMAIL, ADMIN_PASSWORD  (required for production)
    """
    try:
        from .db import get_db
        from sqlalchemy import text
        import pyotp

        conn = get_db()

        # users table (fields used across the app)
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_type TEXT,
                    username TEXT UNIQUE,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    mfa_secret TEXT,
                    permissions TEXT,
                    approved_by_ceo BOOLEAN DEFAULT FALSE,
                    hire_date DATE,
                    salary NUMERIC,
                    role TEXT,
                    account_locked BOOLEAN DEFAULT FALSE,
                    failed_attempts INTEGER DEFAULT 0,
                    last_login TIMESTAMP,
                    org_id INTEGER,
                    tin TEXT,
                    institution_name TEXT,
                    address TEXT,
                    phone TEXT,
                    region TEXT,
                    city TEXT
                )
                """
            )
        )

        # webauthn credentials
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS webauthn_credentials (
                    credential_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    org_id INTEGER,
                    public_key BYTEA NOT NULL,
                    sign_count INTEGER DEFAULT 0
                )
                """
            )
        )
        conn.commit()

        # seed admin if table empty
        cur = conn.execute(text("SELECT COUNT(*) AS c FROM users"))
        count = cur.fetchone()["c"]
        if count == 0:
            admin_email = os.getenv("ADMIN_EMAIL", "").strip()
            admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
            if not admin_email or not admin_password:
                app.logger.warning(
                    "No users and ADMIN_EMAIL/ADMIN_PASSWORD not set; skipping admin seed."
                )
                return

            from .utils import hash_password  # local import to avoid cycles
            mfa_secret = pyotp.random_base32()
            conn.execute(
                text(
                    """
                    INSERT INTO users (user_type, username, email, password_hash, mfa_secret, permissions, approved_by_ceo, role)
                    VALUES (:ut, :un, :em, :ph, :mfa, :perm, TRUE, :role)
                    """
                ),
                {
                    "ut": "employee",
                    "un": admin_email,
                    "em": admin_email,
                    "ph": hash_password(admin_password),
                    "mfa": mfa_secret,
                    "perm": "user_management,put_order,my_orders,order_status,maintenance_request,maintenance_status,message",
                    "role": "Admin",
                },
            )
            conn.commit()
            app.logger.warning(
                "Seeded first admin user %s. TOTP secret: %s (store in authenticator).",
                admin_email,
                mfa_secret,
            )
    except Exception as e:
        app.logger.warning("core tables/admin bootstrap skipped: %s", e)


def create_app(test_config: Optional[dict] = None) -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", os.urandom(32)),
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        WTF_CSRF_TIME_LIMIT=None,
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", os.urandom(32)),
        JWT_TOKEN_LOCATION=["headers"],
        JWT_COOKIE_SECURE=True,
        MFA_ISSUER=os.getenv("MFA_ISSUER", "ERP-BERHAN"),
        WEBAUTHN_RP_ID=os.getenv("WEBAUTHN_RP_ID", "erp-berhan-backend.onrender.com"),
        WEBAUTHN_RP_NAME=os.getenv("WEBAUTHN_RP_NAME", "ERP-BERHAN"),
        WEBAUTHN_ORIGIN=os.getenv("WEBAUTHN_ORIGIN", "https://erp-berhan-backend.onrender.com"),
        CACHE_TYPE=os.getenv("CACHE_TYPE", "null"),
    )
    if test_config:
        app.config.update(test_config)

    _configure_logging(app)

    # Make both erp/templates and repo-root/templates available
    repo_root = os.path.dirname(os.path.dirname(__file__))
    root_templates = os.path.join(repo_root, "templates")
    if os.path.isdir(root_templates):
        app.jinja_loader = ChoiceLoader([  # type: ignore[attr-defined]
            app.jinja_loader,
            FileSystemLoader(root_templates),
        ])
        app.logger.info("Added repo-root templates path: %s", root_templates)

    # Extensions
    try:
        cache.init_app(app)
    except Exception as e:
        app.logger.warning("Cache init skipped: %s", e)
    limiter.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)  # gevent
    oauth.init_app(app)
    _register_oauth_clients(app)

    # DB bootstraps (idempotent)
    _maybe_bootstrap_regions(app)
    _maybe_bootstrap_core_tables_and_admin(app)

    # Blueprints
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    @app.route("/")
    def index():
        return redirect(url_for("auth.choose_login"))

    @app.route("/favicon.ico")
    def favicon():
        return "", 204

    return app


__all__ = ["create_app", "socketio"]
