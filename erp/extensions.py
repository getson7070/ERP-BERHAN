# erp/extensions.py
from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_caching import Cache
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_cors import CORS

# Core extensions (created unbound; configured in create_app)
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()

# Limiter v3.x: configure via app.config in create_app, then init_app(app)
# Use a simple global key func unless you have per-user identification
limiter = Limiter(key_func=lambda: "global")

cache = Cache()
mail = Mail()
socketio = SocketIO()
cors = CORS()

__all__ = [
    "db",
    "migrate",
    "csrf",
    "login_manager",
    "limiter",
    "cache",
    "mail",
    "socketio",
    "cors",
]
