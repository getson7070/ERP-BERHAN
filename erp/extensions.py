# erp/extensions.py
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

# create Limiter & SocketIO without app, then init in init_extensions()
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

def init_extensions(app):
    # DB / Migrate
    db.init_app(app)
    migrate.init_app(app, db)

    # Cache
    cache.init_app(app, config={
        "CACHE_TYPE": os.getenv("CACHE_TYPE", "SimpleCache"),
        "CACHE_DEFAULT_TIMEOUT": int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")),
    })

    # Mail
    mail.init_app(app)

    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Limiter (read config from env to avoid parse errors)
    storage_uri = os.getenv("FLASK_LIMITER_STORAGE_URI") or os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    default_limits = [s.strip() for s in os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second").split(";") if s.strip()]
    app.config.setdefault("RATELIMIT_STORAGE_URI", storage_uri)
    app.config.setdefault("RATELIMIT_DEFAULT", default_limits)
    limiter.init_app(app)

    # SocketIO (optional Redis queue)
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    socketio.init_app(
        app,
        message_queue=os.getenv("SOCKETIO_REDIS_URL"),
        cors_allowed_origins=[o.strip() for o in cors_origins.split(",")] if cors_origins else "*",
    )
