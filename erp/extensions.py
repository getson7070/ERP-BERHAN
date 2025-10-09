from __future__ import annotations
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, AnonymousUserMixin
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
cache = Cache(config={"CACHE_TYPE": "SimpleCache"})
mail = Mail()
# Create real objects at import-time so decorators never crash
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

def init_extensions(app: Flask) -> None:
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("SESSION_COOKIE_SECURE", True)
    app.config.setdefault("PREFERRED_URL_SCHEME", "https")
    app.config.setdefault("RATELIMIT_ENABLED", True)

    CORS(app, resources={r"*": {"origins": "*"}})

    redis_url = os.getenv("REDIS_URL") or os.getenv("RATELIMIT_STORAGE_URI")
    if redis_url:
        app.config["SOCKETIO_MESSAGE_QUEUE"] = redis_url

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app)

def register_blueprints(app: Flask) -> None:
    # Import inside function to avoid import-time side effects
    from .routes.main import bp as main_bp
    from .routes.auth import auth_bp
    from .routes.api import api_bp
    # Import others only if they exist in your codebase:
    try:
        from .routes.orders import bp as orders_bp
        app.register_blueprint(orders_bp)
    except Exception:
        pass
    try:
        from .routes.tenders import bp as tenders_bp
        app.register_blueprint(tenders_bp)
    except Exception:
        pass

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp)
