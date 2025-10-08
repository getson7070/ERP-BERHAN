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
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

# NOTE: In Flask-Limiter 3.x don't pass default_limits into the ctor/init_app
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("REDIS_URL", "memory://"),
    default_limits=None,
)

def init_extensions(app):
    # sane defaults so the app boots even without env vars
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "dev"))
    # Render sets DATABASE_URL; old Heroku format may be 'postgres://'
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", db_url or "sqlite:///instance/app.db")
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # caching + rate limiting
    app.config.setdefault("CACHE_TYPE", "SimpleCache")
    app.config.setdefault("RATELIMIT_STORAGE_URI", os.getenv("REDIS_URL", "memory://"))
    app.config.setdefault("RATELIMIT_HEADERS_ENABLED", True)
    app.config.setdefault("RATELIMIT_DEFAULTS", ["300 per minute", "30 per second"])

    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app, message_queue=os.getenv("REDIS_URL"))

    login_manager.login_view = "auth.login"
    return app
