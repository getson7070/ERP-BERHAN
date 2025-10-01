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

db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()
limiter = Limiter(key_func=get_remote_address)  # storage from app.config if set
cors = CORS()

cache = Cache()
compress = Compress()
csrf = CSRFProtect()
babel = Babel()
jwt = JWTManager()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

def init_extensions(app):
    """Initialize all Flask extensions with the given app."""
    db.init_app(app)
    migrate.init_app(app, db)

    oauth.init_app(app)

    # Flask-Limiter reads RATELIMIT_* from app.config; init with app
    limiter.init_app(app)

    # CORS: allow env-configured origins or '*'
    origins = app.config.get("CORS_ORIGINS", "*")
    if isinstance(origins, str) and origins != "*":
        origins = [o.strip() for o in origins.split(",") if o.strip()]
    cors.init_app(app, resources={r"/*": {"origins": origins}})

    cache.init_app(app)
    compress.init_app(app)
    csrf.init_app(app)
    babel.init_app(app)
    jwt.init_app(app)

    # Optional Redis queue for Socket.IO if provided, else in-process
    socketio.init_app(app, message_queue=app.config.get("SOCKETIO_MESSAGE_QUEUE"))

__all__ = [
    "db","migrate","oauth","limiter","cors",
    "cache","compress","csrf","babel","jwt","socketio",
    "init_extensions",
]
