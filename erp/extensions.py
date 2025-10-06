# erp/extensions.py
import os
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

# Create Limiter & SocketIO without an app; finalize in init_extensions()
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

def _coerce_default_limits(value: str) -> str:
    """
    Accept either a semicolon-separated string (preferred for env),
    or a Python-list-like string, and return a semicolon-separated string
    that Flask-Limiter 3.x understands.
    """
    if not value:
        return "300 per minute; 30 per second"
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        # Turn "['300 per minute','30 per second']" into "300 per minute; 30 per second"
        inner = value[1:-1]
        parts = [p.strip().strip("'").strip('"') for p in inner.split(",")]
        parts = [p for p in parts if p]
        return "; ".join(parts) if parts else "300 per minute; 30 per second"
    # already a string like "300 per minute; 30 per second"
    return value

def init_extensions(app):
    # --- DB / Migrate ---
    db.init_app(app)
    migrate.init_app(app, db)

    # --- Cache ---
    cache.init_app(app, config={
        "CACHE_TYPE": os.getenv("CACHE_TYPE", "SimpleCache"),
        "CACHE_DEFAULT_TIMEOUT": int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")),
    })

    # --- Mail ---
    mail.init_app(app)

    # --- Login Manager ---
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # --- Rate Limiter (Flask-Limiter 3.x) ---
    storage_uri = os.getenv("FLASK_LIMITER_STORAGE_URI") or os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    default_limits_str = _coerce_default_limits(os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second"))
    # IMPORTANT: configure on app.config; do NOT pass kwargs to init_app
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
