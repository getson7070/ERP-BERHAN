# erp/extensions.py
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

# Rate limiting storage
def _rate_limit_storage_uri():
    # Prefer explicit RATELIMIT_STORAGE_URI (Flask-Limiter standard)
    return (
        os.getenv("RATELIMIT_STORAGE_URI")
        or os.getenv("RATE_LIMIT_STORAGE_URL")  # compatibility
        or os.getenv("REDIS_URL")               # Render default if provided
        or "memory://"
    )

limiter = Limiter(key_func=get_remote_address, storage_uri=_rate_limit_storage_uri())

# SocketIO on eventlet
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins=os.getenv("SOCKETIO_CORS", "*"))

def init_extensions(app):
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app, message_queue=os.getenv("SOCKETIO_MESSAGE_QUEUE"))
    # reasonable defaults
    login_manager.login_view = "auth.login"  # if/when you add auth blueprint
    login_manager.session_protection = "strong"
