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

def _default_limits_factory():
    raw = os.getenv("DEFAULT_RATE_LIMITS", "")
    return [s.strip() for s in raw.split(";") if s.strip()]

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=_default_limits_factory,
    storage_uri=os.getenv("FLASK_LIMITER_STORAGE_URI") or os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
)

_socketio_cors = [s.strip() for s in os.getenv("CORS_ORIGINS", "*").split(",") if s.strip()] or "*"
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins=_socketio_cors)

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)

    cache.init_app(app, config={
        "CACHE_TYPE": os.getenv("CACHE_TYPE", "SimpleCache"),
        "CACHE_DEFAULT_TIMEOUT": int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")),
    })

    mail.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    limiter.init_app(app)

    message_queue = os.getenv("SOCKETIO_MESSAGE_QUEUE") or os.getenv("SOCKETIO_REDIS_URL")
    socketio.init_app(app, message_queue=message_queue, cors_allowed_origins=_socketio_cors)
