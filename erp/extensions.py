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
login_manager = LoginManager()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")


def _coerce_default_limits(raw: str) -> list[str]:
    """
    Accepts env like:
      "300 per minute; 30 per second"
      "300 per minute, 30 per second"
      "['300 per minute', '30 per second']"
    and returns a clean list for RATELIMIT_DEFAULT.
    """
    if not raw:
        return []
    s = raw.strip()
    if s.startswith("[") and s.endswith("]"):
        items = [i.strip(" '\"\t") for i in s.strip("[]").split(",")]
        return [i for i in items if i]
    parts = []
    for chunk in s.replace(",", ";").split(";"):
        val = chunk.strip()
        if val:
            parts.append(val)
    return parts


def init_extensions(app):
    # DB / migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # Cache
    cache.init_app(app, config={
        "CACHE_TYPE": os.getenv("CACHE_TYPE", "SimpleCache"),
        "CACHE_DEFAULT_TIMEOUT": int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")),
    })

    # Mail
    mail.init_app(app)

    # Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Limiter (v3.8 reads from app.config, not kwargs)
    storage_uri = os.getenv("FLASK_LIMITER_STORAGE_URI") or os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    default_limits_raw = os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second")
    app.config.setdefault("RATELIMIT_STORAGE_URI", storage_uri)
    app.config.setdefault("RATELIMIT_DEFAULT", _coerce_default_limits(default_limits_raw))
    limiter.init_app(app)

    # Socket.IO
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    socketio.init_app(
        app,
        message_queue=os.getenv("SOCKETIO_REDIS_URL") or os.getenv("REDIS_URL"),
        cors_allowed_origins=[o.strip() for o in cors_origins.split(",")] if cors_origins else "*",
    )
