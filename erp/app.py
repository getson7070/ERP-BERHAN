import os
from pathlib import Path
from flask import Flask, redirect, url_for
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_compress import Compress
from flask_socketio import SocketIO

from db import get_engine, ensure_schema, RedisClient

# Globals used by other modules
jwt = JWTManager()
cache = Cache()
compress = Compress()
socketio = SocketIO(async_mode="threading")  # no eventlet
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour"])
oauth = None  # initialized lazily in create_app()


def _template_search_paths():
    """
    Look in both:
      - project root /templates   (your repository's main templates)
      - erp/templates             (module-local templates)
    """
    root = Path(__file__).resolve().parents[1]
    return [root / "templates", Path(__file__).resolve().parent / "templates"]


def _register_blueprints(app: Flask) -> None:
    # Auth (required for login flows)
    from .routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    # Main dashboard (register if present; don’t crash if missing)
    try:
        from .routes.main import bp as main_bp
        app.register_blueprint(main_bp)
    except Exception as e:
        app.logger.warning("main blueprint not registered: %s", e)

    # Add other blueprints here if you have them
    # try:
    #     from .routes.api import bp as api_bp
    #     app.register_blueprint(api_bp, url_prefix="/api")
    # except Exception as e:
    #     app.logger.warning("api blueprint not registered: %s", e)


def create_app() -> Flask:
    # Build template search list
    search_paths = _template_search_paths()

    app = Flask(
        __name__,
        template_folder=None,            # we’ll install a ChoiceLoader below
        static_folder="static",          # keep default if you have /static
        instance_relative_config=True,
    )

    # Secret key & config
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", os.urandom(32)),
        JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", os.urandom(32)),
        JWT_TOKEN_LOCATION=["headers"],
        JWT_SECRET_ID=os.environ.get("JWT_SECRET_ID", "v1"),
        # Caching (can be None on Render free tier; just avoid crashes)
        CACHE_TYPE=os.environ.get("CACHE_TYPE", "null"),
        # WebAuthn defaults (override in env if you use them)
        WEBAUTHN_RP_ID=os.environ.get("WEBAUTHN_RP_ID", "localhost"),
        WEBAUTHN_RP_NAME=os.environ.get("WEBAUTHN_RP_NAME", "ERP Berhan"),
        WEBAUTHN_ORIGIN=os.environ.get("WEBAUTHN_ORIGIN"),
        # Rate limits
        RATELIMIT_DEFAULT="200 per hour",
        # OAuth placeholders (used by auth.py)
        OAUTH_USERINFO_URL=os.environ.get("OAUTH_USERINFO_URL", ""),
        MFA_ISSUER=os.environ.get("MFA_ISSUER", "ERP-Berhan"),
    )

    # Jinja: search both /templates and erp/templates
    from jinja2 import ChoiceLoader, FileSystemLoader
    loaders = [FileSystemLoader(str(p)) for p in search_paths if p.exists()]
    if not loaders:
        app.logger.warning("No template directories found in %s", search_paths)
    app.jinja_loader = ChoiceLoader(loaders)

    # Extensions
    jwt.init_app(app)
    limiter.init_app(app)
    try:
        cache.init_app(app)
    except Exception as e:
        app.logger.warning("Cache init warning: %s", e)
    compress.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")  # works fine with gthread

    # Database engine & schema
    engine = get_engine()
    ensure_schema(engine)  # <— creates users, regions_cities, webauthn_credentials if missing

    # Minimal Redis client sanity check for rate limiting & auth backoff
    RedisClient.ensure_connection(app)  # will not crash if Redis_URL missing; logs a warning

    # Blueprints
    _register_blueprints(app)

    # Default route -> login chooser
    @app.route("/")
    def index():
        return redirect(url_for("auth.choose_login"))

    return app
