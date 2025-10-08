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
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")
limiter = Limiter(key_func=get_remote_address)

def _coalesce_database_uri(app) -> None:
    uri = (
        app.config.get("SQLALCHEMY_DATABASE_URI")
        or os.getenv("SQLALCHEMY_DATABASE_URI")
        or os.getenv("DATABASE_URL")
    )
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    if uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = uri
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

def init_extensions(app):
    # DB
    _coalesce_database_uri(app)
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    db.init_app(app)
    migrate.init_app(app, db)

    # Cache
    app.config.setdefault("CACHE_TYPE", "SimpleCache")
    cache.init_app(app)

    # Mail
    mail.init_app(app)

    # Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login_page"

    @login_manager.user_loader
    def load_user(user_id):
        try:
            from .models import User  # late import
            return User.query.get(int(user_id))
        except Exception:
            return None

    # CSRF
    csrf.init_app(app)

    # Limiter 3.x
    app.config.setdefault(
        "RATELIMIT_DEFAULT",
        os.getenv("DEFAULT_RATE_LIMITS", "300 per minute;30 per second"),
    )
    app.config.setdefault(
        "RATELIMIT_STORAGE_URI",
        os.getenv("RATELIMIT_STORAGE_URI", os.getenv("REDIS_URL", "memory://")),
    )
    limiter.init_app(app)

    # Socket.IO
    socketio.init_app(app, message_queue=os.getenv("REDIS_URL"), cors_allowed_origins="*")
