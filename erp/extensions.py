# erp/extensions.py
from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Flask-Limiter is optional but expected by routes/api.py
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except Exception:  # package might be missing at build time
    Limiter = None  # type: ignore
    def get_remote_address():  # minimal fallback to satisfy typing
        return "127.0.0.1"     # not used if Limiter is None

# Flask-SocketIO is optional (present in your requirements); make it safe too
try:
    from flask_socketio import SocketIO
except Exception:
    SocketIO = None  # type: ignore

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

# Expose these names so `from erp.extensions import limiter` works:
limiter = Limiter(key_func=get_remote_address) if Limiter else None
socketio = SocketIO(async_mode="eventlet") if SocketIO else None
