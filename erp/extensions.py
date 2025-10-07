# erp/extensions.py
import ast
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

# Create Limiter without app; config will be picked up in init_app
limiter = Limiter(key_func=get_remote_address)


def _normalize_rate_limits(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip()
    if v.startswith("[") and v.endswith("]"):
        try:
            parsed = ast.literal_eval(v)
            if isinstance(parsed, (list, tuple)):
                cleaned = [str(x).strip() for x in parsed if x]
                return ";".join(cleaned)
        except Exception:
            pass
    parts = [p.strip() for p in v.split(";") if p.strip()]
    return ";".join(parts) if parts else None


def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    try:
        from .models import User  # type: ignore
    except Exception:
        User = None

    @login_manager.user_loader
    def load_user(user_id: str):
        if not User:
            return None
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    mail.init_app(app)
    socketio.init_app(app)

    rl = (
        _normalize_rate_limits(app.config.get("DEFAULT_RATE_LIMITS"))
        or _normalize_rate_limits(app.config.get("RATELIMIT_DEFAULT"))
    )
    if rl:
        app.config["RATELIMIT_DEFAULT"] = rl

    storage_uri = app.config.get("RATELIMIT_STORAGE_URI") or app.config.get("FLASK_LIMITER_STORAGE_URI")
    if storage_uri:
        app.config["RATELIMIT_STORAGE_URI"] = storage_uri

    limiter.init_app(app)
