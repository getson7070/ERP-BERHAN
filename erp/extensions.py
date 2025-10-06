# erp/extensions.py
import os
from typing import List, Union

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- Core extension singletons (created once, bound to app in init_extensions) ---
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
login_manager = LoginManager()
mail = Mail()
socketio = SocketIO(async_mode="eventlet")  # CORS configured in init_extensions()


# --- Rate limiting (Flask-Limiter 3.8 API) --------------------------------------
def _parse_default_limits(env_val: str) -> List[str]:
    """
    Accepts a semicolon/comma separated string like:
      "300 per minute; 30 per second"
    and returns:
      ["300 per minute", "30 per second"]

    Any blank chunks are ignored. If someone accidentally sets a bare number
    like "3", it's ignored (as it cannot be parsed by 'limits').
    """
    if not env_val:
        return []
    # split on ; or ,
    chunks = []
    for part in env_val.replace(",", ";").split(";"):
        s = part.strip()
        # drop obviously bad values like plain digits without a unit
        if not s or s.isdigit():
            continue
        chunks.append(s)
    return chunks


# Build limiter configuration from env *before* binding to the app
_DEFAULT_LIMITS_STR = os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second")
_DEFAULT_LIMITS = _parse_default_limits(_DEFAULT_LIMITS_STR)

_STORAGE_URI = (
    os.getenv("FLASK_LIMITER_STORAGE_URI")
    or os.getenv("RATELIMIT_STORAGE_URI")
    or "memory://"
)

# Construct Limiter with defaults at creation time (required in v3.8)
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_STORAGE_URI,
    default_limits=_DEFAULT_LIMITS,  # list[str]
)


# --- Bind all extensions to the Flask app ---------------------------------------
def init_extensions(app):
    """
    Initialize and attach all extensions to the Flask app instance.
    This function is called from create_app().
    """
    # Reasonable Cache defaults if not provided by env
    app.config.setdefault("CACHE_TYPE", os.getenv("CACHE_TYPE", "SimpleCache"))
    app.config.setdefault(
        "CACHE_DEFAULT_TIMEOUT",
        int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")),
    )

    # LoginManager minimal setup
    # If you have a specific endpoint, adjust (e.g., 'auth.login')
    login_manager.login_view = "auth.login"

    # Initialize each extension with the app
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # SocketIO CORS
    origins_env = os.getenv("CORS_ORIGINS", "*").strip()
    if origins_env == "*" or not origins_env:
        allowed_origins: Union[str, List[str]] = "*"
    else:
        allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
    socketio.init_app(app, cors_allowed_origins=allowed_origins)

    # Limiter: already constructed with defaults & storage_uri.
    # For v3.8 do NOT pass default_limits= here; just bind to app.
    limiter.init_app(app)


__all__ = [
    "db",
    "migrate",
    "cache",
    "limiter",
    "login_manager",
    "mail",
    "socketio",
    "init_extensions",
]
