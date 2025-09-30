# erp/app.py
import os
from typing import List, Optional

from flask import Flask, jsonify, redirect, url_for
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix

# App extensions (these are defined in erp/extensions.py in your repo)
from .extensions import db, limiter, oauth, jwt, cache, compress, csrf, babel


# Socket.IO instance exported for wsgi.py to use
socketio = SocketIO(
    async_mode="eventlet",
    message_queue=os.getenv("SOCKETIO_MESSAGE_QUEUE"),  # works with/without Redis
    cors_allowed_origins=os.getenv("CORS_ORIGINS", "*"),
    logger=False,
    engineio_logger=False,
)


def _as_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    # Accept comma-separated origins
    return [v.strip() for v in value.split(",") if v.strip()]


def _load_config(app: Flask) -> None:
    """Load config solely from environment to keep Render predictable."""
    app.config["ENV"] = os.getenv("APP_ENV", os.getenv("FLASK_ENV", "production"))
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", os.getenv("SECRET_KEY", "change-me"))
    app.config["SECURITY_PASSWORD_SALT"] = os.getenv("SECURITY_PASSWORD_SALT", "change-me-salt")

    # Database (some modules use SQLAlchemy, others use a raw engine via erp/db.py)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///instance/erp.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # JWT
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET", app.config["SECRET_KEY"])
    app.config["JWT_SECRET_ID"] = os.getenv("JWT_SECRET_ID", "v1")
    app.config["JWT_TOKEN_LOCATION"] = _as_list(os.getenv("JWT_TOKEN_LOCATION", "headers,cookies"))

    # Rate limiting
    app.config["RATELIMIT_STORAGE_URI"] = os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL") or "memory://"
    app.config["RATELIMIT_DEFAULT"] = os.getenv("RATELIMIT_DEFAULT", "60 per minute")

    # Redis/Backoff settings used in auth.py
    app.config["LOCK_WINDOW"] = int(os.getenv("LOCK_WINDOW", "300"))  # seconds to keep fail counters
    app.config["LOCK_THRESHOLD"] = int(os.getenv("LOCK_THRESHOLD", "5"))
    app.config["ACCOUNT_LOCK_SECONDS"] = int(os.getenv("ACCOUNT_LOCK_SECONDS", "900"))
    app.config["MAX_BACKOFF"] = int(os.getenv("MAX_BACKOFF", "60"))
    app.config["JWT_REVOCATION_TTL"] = int(os.getenv("JWT_REVOCATION_TTL", "3600"))

    # MFA / WebAuthn
    app.config["MFA_ISSUER"] = os.getenv("MFA_ISSUER", "ERP-BERHAN")
    app.config["WEBAUTHN_RP_ID"] = os.getenv("WEBAUTHN_RP_ID", "onrender.com")
    app.config["WEBAUTHN_RP_NAME"] = os.getenv("WEBAUTHN_RP_NAME", "ERP Berhan")
    app.config["WEBAUTHN_ORIGIN"] = os.getenv("WEBAUTHN_ORIGIN")  # optional

    # OAuth (Authlib)
    app.config["OAUTH_CLIENT_ID"] = os.getenv("OAUTH_CLIENT_ID")
    app.config["OAUTH_CLIENT_SECRET"] = os.getenv("OAUTH_CLIENT_SECRET")
    app.config["OAUTH_DISCOVERY_URL"] = os.getenv("OAUTH_DISCOVERY_URL")
    app.config["OAUTH_USERINFO_URL"] = os.getenv("OAUTH_USERINFO_URL")
    app.config["OAUTH_PROVIDER"] = os.getenv("OAUTH_PROVIDER", "sso")

    # CORS + proxies
    app.config["CORS_ORIGINS"] = os.getenv("CORS_ORIGINS", "*")


def _init_extensions(app: Flask) -> None:
    """Initialize all extensions against the app."""
    # Respect X-Forwarded headers on Render
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)  # type: ignore

    # Optional/available extensions
    try:
        db.init_app(app)
    except Exception:
        pass

    try:
        cache.init_app(app)
    except Exception:
        pass

    try:
        compress.init_app(app)
    except Exception:
        pass

    try:
        csrf.init_app(app)
    except Exception:
        pass

    try:
        babel.init_app(app)
    except Exception:
        pass

    try:
        jwt.init_app(app)
    except Exception:
        pass

    try:
        limiter.init_app(app)
    except Exception:
        pass

    try:
        # Configure OAuth (Authlib)
        oauth.init_app(app)
        if app.config.get("OAUTH_DISCOVERY_URL"):
            oauth.register(
                name="sso",
                server_metadata_url=app.config["OAUTH_DISCOVERY_URL"],
                client_id=app.config.get("OAUTH_CLIENT_ID"),
                client_secret=app.config.get("OAUTH_CLIENT_SECRET"),
                client_kwargs={"scope": "openid email profile"},
            )
    except Exception:
        pass

    # Attach socketio AFTER app is configured
    socketio.init_app(app)


def _security_hardening(app: Flask) -> None:
    """Conservative security settings that won’t block your templates."""
    try:
        from flask_talisman import Talisman
        Talisman(
            app,
            content_security_policy=None,  # don’t block existing inline scripts/styles
            force_https=True,
            frame_options="SAMEORIGIN",
            strict_transport_security=True,
        )
    except Exception:
        # Talisman is optional; if not available we just skip it
        pass


def create_app() -> Flask:
    """Application factory used by wsgi.py and gunicorn."""
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    _load_config(app)
    _init_extensions(app)
    _security_hardening(app)

    # Blueprints: use the actual exported names from the modules
    from .routes.auth import bp as auth_bp
    from .routes.dashboard_customize import bp as dashboard_bp

    # Do NOT add a second url_prefix for auth; some routes already include "/auth/..."
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)  # this blueprint already sets url_prefix="/dashboard"

    # Health/status endpoint for Render checks
    @app.get("/status")
    def status():
        return jsonify({"status": "ok"}), 200

    # User entry points
    @app.route("/")
    def index():
        # Route users to the login chooser UI
        return redirect(url_for("auth.choose_login"))

    @app.route("/login")
    def login_redirect():
        # Convenience path if bookmarks point here
        return redirect(url_for("auth.choose_login"))

    return app
