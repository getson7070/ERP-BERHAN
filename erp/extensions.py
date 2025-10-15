from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
socketio = SocketIO(cors_allowed_origins="*")

login_manager.login_view = "auth.login"

# Global rate limiter (default: 200/day; 50/hour)
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]) 
