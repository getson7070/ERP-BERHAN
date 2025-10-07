# erp/extensions.py
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_login import LoginManager, UserMixin
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
login_manager = LoginManager()
# 3.x: construct Limiter without passing default_limits here
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

class Anonymous(UserMixin):
    """So templates can safely access current_user without user_loader blowing up."""
    pass

def init_extensions(app):
    # --- Cache ---
    app.config.setdefault("CACHE_TYPE", os.getenv("CACHE_TYPE", "SimpleCache"))
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")))
    cache.init_app(app)

    # --- DB / Migrations ---
    db.init_app(app)
    migrate.init_app(app, db)

    # --- Login ---
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.anonymous_user = Anonymous

    # Provide a no-op user_loader so Flask-Login doesn't raise at template render.
    @login_manager.user_loader
    def load_user(user_id):
        # TODO: replace with real lookup when you add a User model
        return None

    # --- Rate limiting (Flask-Limiter 3.x) ---
    # Accept "300 per minute; 30 per second" or a list ["300 per minute", "30 per second"]
    defaults = os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second")
    if isinstance(defaults, str):
        default_limits = [s.strip() for s in defaults.split(";") if s.strip()]
    else:
        default_limits = list(defaults)

    app.config["RATELIMIT_DEFAULTS"] = default_limits
    app.config.setdefault("RATELIMIT_STORAGE_URI", os.getenv("RATELIMIT_STORAGE_URI", "memory://"))

    limiter.init_app(app)  # no default_limits kwarg in 3.x

    # --- Socket.IO ---
    socketio.init_app(app, message_queue=os.getenv("SOCKETIO_MESSAGE_QUEUE"))
