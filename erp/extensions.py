from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

from flask_caching import Cache
from flask_compress import Compress
from flask_wtf import CSRFProtect
from flask_babel import Babel
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO


# Core database & migrations
db = SQLAlchemy()
migrate = Migrate()

# OAuth client
oauth = OAuth()

# Rate limit & CORS
limiter = Limiter(key_func=get_remote_address)
cors = CORS()

# Optional goodies
cache = Cache()
compress = Compress()
csrf = CSRFProtect()
babel = Babel()
jwt = JWTManager()

# Realtime
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")


def init_extensions(app):
    """
    Initialize all Flask extensions with the given app.
    This function is required by erp/__init__.py and erp/app.py.
    """
    # Core
    db.init_app(app)
    migrate.init_app(app, db)

    # OAuth
    oauth.init_app(app)

    # Limits & CORS
    limiter.init_app(app)
    origins = app.config.get("CORS_ORIGINS", "*")
    if isinstance(origins, str) and origins != "*":
        origins = [o.strip() for o in origins.split(",") if o.strip()]
    cors.init_app(app, resources={r"/*": {"origins": origins}})

    # Optional bits
    cache.init_app(app)
    compress.init_app(app)
    csrf.init_app(app)
    babel.init_app(app)
    jwt.init_app(app)

    # Socket.IO (optionally use Redis message queue if provided)
    socketio.init_app(app, message_queue=app.config.get("SOCKETIO_MESSAGE_QUEUE"))


__all__ = [
    "db",
    "migrate",
    "oauth",
    "limiter",
    "cors",
    "cache",
    "compress",
    "csrf",
    "babel",
    "jwt",
    "socketio",
    "init_extensions",
]
