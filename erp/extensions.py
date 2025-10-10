# erp/extensions.py
from __future__ import annotations

import os
from typing import Optional, Callable

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- Core ORM & migrations ---
db: SQLAlchemy = SQLAlchemy()
migrate: Migrate = Migrate()

# --- Security / forms ---
csrf: CSRFProtect = CSRFProtect()
login_manager: LoginManager = LoginManager()

# --- Mail ---
mail: Mail = Mail()

# --- Rate limiting ---
# Use storage from env (Render: memory://) and default limits if provided.
_default_limits = os.getenv("DEFAULT_RATE_LIMITS")  # e.g. "300 per minute; 30 per second"
_storage_uri = os.getenv("RATELIMIT_STORAGE_URI", os.getenv("FLASK_LIMITER_STORAGE_URI", "memory://"))

limiter: Limiter = Limiter(
    key_func=get_remote_address,
    default_limits=_default_limits.split(";") if _default_limits else None,
    storage_uri=_storage_uri,
)

# --- Websocket ---
# eventlet is installed; keep async_mode explicit to avoid auto-detection surprises.
socketio: SocketIO = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

# --- CORS (optional init in app factory) ---
cors: CORS = CORS()

# --- Caching (optional; SimpleCache by default via env) ---
# Render env has:
#   CACHE_TYPE=SimpleCache
#   CACHE_DEFAULT_TIMEOUT=300
cache: Cache = Cache()

__all__ = [
    "db",
    "migrate",
    "csrf",
    "login_manager",
    "mail",
    "limiter",
    "socketio",
    "cors",
    "cache",
]
