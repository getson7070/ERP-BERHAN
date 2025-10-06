# erp/extensions.py
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
socketio = SocketIO(async_mode="eventlet")  # eventlet stack

def _normalize_rate_limits(val):
    """
    Accept list/tuple or string; return a semicolon-separated string usable by Flask-Limiter.
    Also tolerates a 'stringified list' like "['300 per minute', '30 per second']".
    """
    if not val:
        return ""
    if isinstance(val, (list, tuple)):
        return "; ".join(val)

    s = str(val).strip()
    # if someone provided a stringified list, strip [ ] and quotes, turn commas into semicolons
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    s = s.replace("'", "").replace('"', "")
    s = s.replace(",", ";")
    return s

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # SocketIO (optional Redis message queue)
    socketio.init_app(app, message_queue=app.config.get("REDIS_URL"))

    # Limiter: read from config and normalize
    limits_value = app.config.get("DEFAULT_RATE_LIMITS")
    limits_string = _normalize_rate_limits(limits_value)
    limiter = Limiter(key_func=get_remote_address, default_limits=limits_string)
    limiter.init_app(app)

    # expose for imports expecting these names
    app.extensions["limiter"] = limiter
