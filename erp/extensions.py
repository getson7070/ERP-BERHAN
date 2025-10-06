import os
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
socketio = SocketIO(async_mode="eventlet")


def _limits_to_list(val):
    """
    Normalize DEFAULT_RATE_LIMITS from env into a list[str].
    Accepts:
      - list/tuple: ['300 per minute', '30 per second']
      - '300 per minute; 30 per second'
      - '300 per minute, 30 per second'
      - "['300 per minute','30 per second']"
    Returns [] if empty/None.
    """
    if not val:
        return []
    if isinstance(val, (list, tuple)):
        return [str(x).strip() for x in val if str(x).strip()]
    s = str(val).strip()
    # handle stringified list
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    # drop quotes and split on ; or ,
    s = s.replace('"', "").replace("'", "")
    parts = [p.strip() for p in s.replace(";", ",").split(",")]
    return [p for p in parts if p]


# Build defaults at import time (required by Flask-Limiter 3.8)
DEFAULT_LIMITS_LIST = _limits_to_list(
    os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second")
)

# IMPORTANT: pass list of strings to the constructor
limiter = Limiter(key_func=get_remote_address, default_limits=DEFAULT_LIMITS_LIST)


def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    socketio.init_app(app, message_queue=app.config.get("REDIS_URL"))

    # No default_limits here (3.8 doesn't accept that kwarg on init_app)
    limiter.init_app(app)
