import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")
csrf = CSRFProtect()
login_manager = LoginManager()

def _parse_default_limits():
    # ENV can be like: "300 per minute; 30 per second"
    val = os.environ.get("DEFAULT_RATE_LIMITS", "").strip()
    if val:
        return [part.strip() for part in val.split(";") if part.strip()]
    # Safe fallback:
    return ["300 per minute", "30 per second"]

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=_parse_default_limits(),
    storage_uri=os.environ.get("FLASK_LIMITER_STORAGE_URI", os.environ.get("RATELIMIT_STORAGE_URI", "memory://")),
)
