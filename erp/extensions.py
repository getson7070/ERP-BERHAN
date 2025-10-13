# erp/extensions.py — complete
from __future__ import annotations
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_cors import CORS
from flask_mail import Mail
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["1000/hour"])
cache = Cache(config={"CACHE_TYPE": "SimpleCache"})
cors = CORS()
mail = Mail()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

def init_extensions(app):
    # security defaults
    app.config.setdefault("SESSION_COOKIE_SECURE", True)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")

    # rate limit storage (env override in Render)
    storage_uri = app.config.get("FLASK_LIMITER_STORAGE_URI", "memory://")
    limiter.storage_uri = storage_uri

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cache.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": app.config.get("CORS_ORIGINS") or "*"}})
    mail.init_app(app)
    socketio.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.session_protection = "strong"
