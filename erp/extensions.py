# erp/extensions.py
import eventlet
eventlet.monkey_patch()

import os
import re
from typing import List, Optional

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Create extension instances (no app bound yet)
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
login_manager = LoginManager()
mail = Mail()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")
# Do NOT pass app here; we will call init_app later.
limiter = Limiter(key_func=get_remote_address)

def _parse_default_limits(value: Optional[str]) -> List[str]:
    """
    Convert env string like '300 per minute; 30 per second'
    into ['300 per minute', '30 per second'].
    Ignores empty chunks and things that don't look like a rate (must contain 'per').
    """
    if not value:
        return []
    chunks = re.split(r"[;,]", value)
    out: List[str] = []
    for c in chunks:
        s = c.strip()
        if not s:
            continue
        if "per" not in s:
            # Avoid stray tokens like '3'
            continue
        out.append(s)
    return out

def init_extensions(app):
    """
    Bind all extensions to the Flask app. Safe for Flask-Limiter 3.x.
    """

    # ---- Cache (use a real default, not setdefault(None))
    app.config["CACHE_TYPE"] = os.getenv(
        "CACHE_TYPE", app.config.get("CACHE_TYPE") or "SimpleCache"
    )
    app.config["CACHE_DEFAULT_TIMEOUT"] = int(
        os.getenv("CACHE_DEFAULT_TIMEOUT", app.config.get("CACHE_DEFAULT_TIMEOUT") or 300)
    )

    # ---- Rate limiting defaults via CONFIG (3.x way)
    default_limits_list = _parse_default_limits(
        os.getenv("DEFAULT_RATE_LIMITS") or app.config.get("DEFAULT_RATE_LIMITS")
    )
    if default_limits_list:
        # Flask-Limiter reads this key in 3.x+
        app.config["RATELIMIT_DEFAULT"] = default_limits_list

    # Choose storage backend (memory:// is OK to start; for prod prefer Redis)
    storage_uri = (
        os.getenv("FLASK_LIMITER_STORAGE_URI")
        or os.getenv("RATELIMIT_STORAGE_URI")
        or app.config.get("FLASK_LIMITER_STORAGE_URI")
        or app.config.get("RATELIMIT_STORAGE_URI")
        or "memory://"
    )

    # ---- Init core extensions
    cache.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)

    # ---- Init limiter (NO default_limits kw here; NO limiter.default_limits(...) calls)
    # We configure defaults via app.config['RATELIMIT_DEFAULT'] above.
    limiter.storage_uri = storage_uri
    limiter.init_app(app)

    # ---- SocketIO message queue (optional)
    mq = os.getenv("REDIS_URL") or app.config.get("REDIS_URL")
    if mq:
        socketio.init_app(app, message_queue=mq, cors_allowed_origins=app.config.get("CORS_ORIGINS", "*"))
    else:
        socketio.init_app(app, cors_allowed_origins=app.config.get("CORS_ORIGINS", "*"))
