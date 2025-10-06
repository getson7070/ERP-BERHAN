# erp/extensions.py
import os
import ast

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
mail = Mail()
login_manager = LoginManager()

# Create Limiter & SocketIO without app; configure in init_extensions()
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")


def _limits_to_config_str(value: str | None) -> str:
    """
    Accept either:
      - "300 per minute; 30 per second"   (semicolon-separated string)
      - "['300 per minute', '30 per second']" (list-like string)
    Return a clean semicolon-separated string for app.config.
    """
    if not value:
        return "300 per minute; 30 per second"

    s = value.strip()
    if s.startswith("[") and s.endswith("]"):
        try:
            parsed = ast.literal_eval(s)
            parts = [str(x).strip() for x in parsed if str(x).strip()]
            return "; ".join(parts) if parts else "300 per minute; 30 per second"
        except Exception:
            return "300 per minute; 30 per second"

    # Already a string form; normalize spaces around semicolons.
    items = [x.strip() for x in s.split(";") if x.strip()]
    return "; ".join(items) if items else "300 per minute; 30 per second"


def init_extensions(app):
    # --- DB / Migrate ---
    db.init_app(app)
    migrate.init_app(app, db)

    # --- Cache ---
    cache.init_app(
        app,
        config={
            "CACHE_TYPE": os.getenv("CACHE_TYPE", "SimpleCache"),
            "CACHE_DEFAULT_TIMEOUT": int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")),
        },
    )

    # --- Mail ---
    mail.init_app(app)

    # --- Login ---
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # --- Limiter (configure via app.config for Flask-Limiter 3.8.x) ---
    storage_uri = (
        os.getenv("FLASK_LIMITER_STORAGE_URI")
        or os.getenv("RATELIMIT_STORAGE_URI")
        or "memory://"
    )
    default_limits_env = os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second")
    default_limits_str = _limits_to_config_str(default_limits_env)

    # IMPORTANT: put values in config; do NOT pass as kwargs to init_app
    app.config["RATELIMIT_STORAGE_URI"] = storage_uri
    app.config["RATELIMIT_DEFAULT"] = default_limits_str

    limiter.init_app(app)

    # --- Socket.IO ---
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    socketio.init_app(
        app,
        message_queue=os.getenv("SOCKETIO_MESSAGE_QUEUE"),
        cors_allowed_origins=[o.strip() for o in cors_origins.split(",")] if cors_origins else "*",
    )
