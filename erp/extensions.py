# erp/extensions.py
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
cache = Cache()

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("FLASK_LIMITER_STORAGE_URI") or os.getenv("RATELIMIT_STORAGE_URI") or "memory://",
    default_limits=[
        l.strip() for l in (os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second").split(";"))
        if l.strip()
    ],
)

socketio = SocketIO(
    async_mode="eventlet",
    cors_allowed_origins=os.getenv("CORS_ORIGINS", "*"),
)
