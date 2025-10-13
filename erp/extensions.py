# erp/extensions.py
from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_caching import Cache
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
cache = Cache()
cors = CORS()
# Limiter is created with default key func; storage taken from app.config during init
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")


def init_extensions(app):
    # Cache
    cache.init_app(app, config={
        "CACHE_TYPE": app.config.get("CACHE_TYPE", "SimpleCache"),
        "CACHE_DEFAULT_TIMEOUT": app.config.get("CACHE_DEFAULT_TIMEOUT", 300),
    })

    # SQLAlchemy & Migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # Mail
    mail.init_app(app)

    # CORS
    origins = app.config.get("CORS_ORIGINS")
    if isinstance(origins, str) and "," in origins:
        origins = [o.strip() for o in origins.split(",")]
    cors.init_app(app, resources={r"/*": {"origins": origins or "*"}})

    # Rate limiter
    storage_uri = app.config.get("FLASK_LIMITER_STORAGE_URI") or app.config.get("RATELIMIT_STORAGE_URI") or "memory://"
    default_limits = app.config.get("DEFAULT_RATE_LIMITS")
    if isinstance(default_limits, str):
        # allow "300 per minute; 30 per second"
        default_limits = [s.strip() for s in default_limits.split(";") if s.strip()]
    limiter.storage_uri = storage_uri
    limiter.init_app(app, default_limits=default_limits or [])

    # Socket.IO
    msg_q = app.config.get("SOCKETIO_MESSAGE_QUEUE")  # optional
    socketio.init_app(app, message_queue=msg_q)

    # Login manager
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # optional, only used if you have that route

    @login_manager.user_loader
    def load_user(user_id: str):
        # Import inside to avoid circulars
        from .models import User
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None
