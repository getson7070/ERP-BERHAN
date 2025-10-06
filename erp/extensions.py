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

def _normalize_rate_limits(val):
    """Accept list/tuple or string; also handle stringified lists.
    Return a semicolon-separated string that Flask-Limiter 3.x accepts."""
    if not val:
        return ""
    if isinstance(val, (list, tuple)):
        return "; ".join(val)
    s = str(val).strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]  # drop brackets from "['a','b']"
    s = s.replace("'", "").replace('"', "")
    s = s.replace(",", ";")
    return s

# Read from env *now* so the instance carries the defaults (3.8 requires constructor)
DEFAULT_LIMITS = _normalize_rate_limits(
    os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second")
)

# IMPORTANT: provide defaults in the constructor (not init_app)
limiter = Limiter(key_func=get_remote_address, default_limits=DEFAULT_LIMITS)

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    socketio.init_app(app, message_queue=app.config.get("REDIS_URL"))

    # No default_limits here — 3.8.0 doesn't accept that kwarg
    limiter.init_app(app)
