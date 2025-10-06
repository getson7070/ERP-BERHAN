# erp/extensions.py
import os, re, warnings

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
login_manager = LoginManager()
mail = Mail()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

# ✅ Instantiate with storage_uri (v3.8+)
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=(
        os.getenv("RATELIMIT_STORAGE_URI")
        or os.getenv("FLASK_LIMITER_STORAGE_URI")
        or "memory://"
    ),
)

def _parse_default_limits(env_value: str):
    """Accept '300 per minute; 30 per second' or CSV/newline."""
    if not env_value:
        return []
    parts = [p.strip() for p in re.split(r"[;,\n]+", env_value) if p.strip()]
    return parts

def init_extensions(app):
    # ✅ Apply cache config BEFORE init
    app.config.setdefault("CACHE_TYPE", os.getenv("CACHE_TYPE", "SimpleCache"))
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")))
    cache.init_app(app)

    # ✅ Init limiter and then register default limits in v3.8
    limiter.init_app(app)
    default_limits = _parse_default_limits(os.getenv("DEFAULT_RATE_LIMITS", ""))
    if default_limits:
        limiter.default_limits(default_limits)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    socketio.init_app(app, message_queue=os.getenv("SOCKETIO_MESSAGE_QUEUE"))
