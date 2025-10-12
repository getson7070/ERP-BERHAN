# erp/extensions.py
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
cache = Cache(config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300})

REDIS_URL = (
    os.environ.get("REDIS_URL")
    or os.environ.get("REDISCLOUD_URL")
    or os.environ.get("UPSTASH_REDIS_URL")
)

# Rate limiter (Redis in prod if available, memory otherwise)
if REDIS_URL:
    limiter = Limiter(key_func=get_remote_address, storage_uri=REDIS_URL, strategy="fixed-window")
else:
    limiter = Limiter(key_func=get_remote_address, storage_uri="memory://", strategy="fixed-window")

# Socket.IO prefers eventlet when available; otherwise threading
try:
    import eventlet  # noqa
    async_mode = "eventlet"
except Exception:
    async_mode = "threading"

socketio = SocketIO(async_mode=async_mode, cors_allowed_origins="*")

def init_app_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app, message_queue=REDIS_URL if REDIS_URL else None)
