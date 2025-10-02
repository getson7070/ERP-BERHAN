# erp/extensions.py
from __future__ import annotations

import os
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_mail import Mail
from flask_wtf import CSRFProtect
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- SQLAlchemy naming convention (works with Alembic & SA 2.x) ---
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

db = SQLAlchemy(metadata=MetaData(naming_convention=NAMING_CONVENTION))
migrate = Migrate()
ma = Marshmallow()
bcrypt = Bcrypt()
csrf = CSRFProtect()
mail = Mail()
cors = CORS()

# Use pure threading; avoids eventlet/gevent entirely
socketio = SocketIO(
    async_mode=os.getenv("SOCKETIO_ASYNC_MODE", "threading"),
    message_queue=os.getenv("SOCKETIO_MESSAGE_QUEUE"),
    cors_allowed_origins="*",
)

# Flask-Limiter v3: storage_uri must be passed to the constructor
_limiter_storage_uri = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
_default_limits_env = os.getenv("DEFAULT_RATE_LIMITS", "")
_default_limits = [s.strip() for s in _default_limits_env.split(",") if s.strip()]

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_limiter_storage_uri,
    default_limits=_default_limits,
)

def init_extensions(app):
    """Bind extensions to the Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})

    # Socket.IO attaches to the app but we keep thread-based async
    socketio.init_app(app)
