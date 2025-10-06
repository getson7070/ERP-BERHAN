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

# Create Limiter & SocketIO without app; finalize in init_extensions()
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")


def _parse_default_limits(env_value: str) -> list[str]:
    """
    Accept either:
      - "300 per minute; 30 per second"   (semicolon-separated string)
      - "['300 per minute', '30 per second']" (list-like string)
    and return a clean list of strings.
    """
    if not env_value:
        return ["300 per minute", "30 per second"]

    env_value = env_value.strip()
    # List-like? Safely parse.
    if env_value.startswith("[") and env_value.endswith("]"):
        try:
            parsed = ast.literal_eval(env_value)
            return [str(s).strip() for s in parsed if str(s).strip()]
        except Exception:
            # Fallback to sane defaults if parsing fails
            return ["300 per minute", "30 per second"]

    # Semicolon-separated
    return [s.strip() for s in env_value.split(";") if s.strip()]


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

    # --- Limiter ---
    storage_uri = os.getenv("FLASK_LIMITER_STORAGE_URI") or os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    limits_env = os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second")
    default_limits = _parse_default_limits(limits_env)

    # IMPORTANT: pass defaults directly here; don't put a list into app.config
    limiter.init_app(
        app,
        storage_uri=storage_uri,
        default_limits=default_limits,
    )

    # --- Socket.IO ---
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    socketio.init_app(
        app,
        message_queue=os.getenv("SOCKETIO_MESSAGE_QUEUE"),
        cors_allowed_origins=[o.strip() for o in cors_origins.split(",")] if cors_origins else "*",
    )
