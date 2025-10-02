# erp/extensions.py
from __future__ import annotations

import os
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_cors import CORS
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from flask_bcrypt import Bcrypt

# ───────────────────────── SQLAlchemy naming convention ───────────────────────
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Create the SQLAlchemy instance with the MetaData that ALREADY has the convention
db = SQLAlchemy(metadata=MetaData(naming_convention=NAMING_CONVENTION))

# Other extensions (instantiated without side effects)
migrate = Migrate()
jwt = JWTManager()
cache = Cache()
bcrypt = Bcrypt()
cors = CORS()
compress = Compress()

# Flask-Limiter 3.x: set storage backend on the Limiter INSTANCE, not in init_app
_limiter_storage = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_limiter_storage,
    enabled=True,          # allow toggling via env later if needed
    default_limits=[],     # define per-route limits with decorators
)

# SocketIO: message queue optional; eventlet is used by Gunicorn workers
socketio = SocketIO(
    async_mode="eventlet",
    message
