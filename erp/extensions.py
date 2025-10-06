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

# Core extensions (singletons)
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
limiter = Limiter(key_func=get_remote_address)
login_manager = LoginManager()
mail = Mail()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

# Provide a safe user_loader so /auth/login can render without exceptions.
# We lazy-import User to avoid circular imports at import time.
@login_manager.user_loader
def _load_user(user_id: str):
    try:
        from .models import User  # type: ignore
    except Exception:
        return None
    try:
        # SQLAlchemy 2.x way to load by PK
        return db.session.get(User, int(user_id))
    except Exception:
        return None

@login_manager.request_loader
def _load_user_from_request(request):
    # Not using token-based auth here; return None so anonymous user is used.
    return None


def init_extensions(app):
    """Bind all extensions to the Flask app (single source of truth)."""

    # ---- DB / migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # ---- Cache
    cache_cfg = {
        "CACHE_TYPE": os.getenv("CACHE_TYPE", "SimpleCache"),
        "CACHE_DEFAULT_TIMEOUT": int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")),
    }
    cache.init_app(app, config=cache_cfg)

    # ---- Flask-Login
    login_manager.init_app(app)
    # This endpoint must exist; adjust if your login view is different
    login_manager.login_view = "auth.login"

    # ---- Flask-Limiter
    storage_uri = os.getenv("FLASK_LIMITER_STORAGE_URI") or os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    default_limits = [
        s.strip() for s in os.getenv("DEFAULT_RATE_LIMITS", "300 per minute; 30 per second").split(";") if s.strip()
    ]
    app.config.setdefault("RATELIMIT_STORAGE_URI", storage_uri)
    app.config.setdefault("RATELIMIT_DEFAULT", default_limits)
    limiter.init_app(app)

    # ---- Mail
    # Make sure Flask-Mail is installed and you set SMTP env vars on Render
    mail.init_app(app)

    # ---- Socket.IO (optionally with Redis message queue)
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    socketio.init_app(
        app,
        message_queue=os.getenv("SOCKETIO_REDIS_URL"),
        cors_allowed_origins=[o.strip() for o in cors_origins.split(",")] if cors_origins else "*",
    )
