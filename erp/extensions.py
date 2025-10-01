# erp/extensions.py
from __future__ import annotations

from authlib.integrations.flask_client import OAuth
from flask_babel import Babel
from flask_caching import Cache
from flask_compress import Compress
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# Core persistence
db = SQLAlchemy()

# Cross-cutting extensions
cache = Cache()
compress = Compress()
csrf = CSRFProtect()
babel = Babel()
jwt = JWTManager()

# Rate limiting & sockets
limiter = Limiter(key_func=get_remote_address, default_limits=[], storage_uri=None)
socketio = SocketIO(cors_allowed_origins="*")  # adjust per your CSP

# OAuth client registry (Authlib)
oauth = OAuth()
