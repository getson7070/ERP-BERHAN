# erp/extensions.py
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

# Exposed name 'limiter' must exist (your imports rely on it)
limiter = Limiter(key_func=get_remote_address, default_limits=[])

cache = Cache()
cors = CORS()
mail = Mail()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

def init_extensions(app) -> None:
    # Config-driven defaults
    limiter.default_limits = [s.strip() for s in app.config.get("DEFAULT_RATE_LIMITS", "").split(";") if s.strip()]
    storage_uri = app.config.get("FLASK_LIMITER_STORAGE_URI", "memory://")
    limiter.storage_uri = storage_uri

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cache.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": app.config.get("CORS_ORIGINS") or "*"}})
    mail.init_app(app)
    socketio.init_app(app)

    # Login defaults
    login_manager.login_view = "auth.login_client"
    login_manager.session_protection = "strong"
