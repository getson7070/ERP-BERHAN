# erp/extensions.py
import os

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
from flask_socketio import SocketIO

# IMPORTANT:
# Do NOT import from flask_jwt_extended at module-top. It defines LocalProxy
# objects that eventlet tries to traverse during monkey_patch. We import it
# lazily in init_extensions() after patching has already happened.

# Core
db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()

# Rate limiting (storage configured in init_extensions)
limiter = Limiter(key_func=get_remote_address)

# CORS
cors = CORS()

# Optional extras
cache = Cache()          # default configured in init_extensions
compress = Compress()
csrf = CSRFProtect()
babel = Babel()

# Will be created lazily in init_extensions
jwt = None  # type: ignore[assignment]

# Realtime (eventlet backend by default)
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")


def init_extensions(app):
    """
    Initialize all Flask extensions with the Flask app.
    Kept centralized so erp.__init__ / erp.app can simply call this.
    """
    # --- Database & migrations ------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)

    # --- OAuth ---------------------------------------------------------------
    oauth.init_app(app)

    # --- CORS ---------------------------------------------------------------
    origins = app.config.get("CORS_ORIGINS", "*")
    if isinstance(origins, str) and origins != "*":
        origins = [o.strip() for o in origins.split(",") if o.strip()]
    cors.init_app(app, resources={r"/*": {"origins": origins}})

    # --- Limiter -------------------------------------------------------------
    # Prefer Redis if available; fall back to in-memory (acceptable for dev)
    storage_uri = app.config.get("RATELIMIT_STORAGE_URI")
    if not storage_uri:
        redis_url = os.getenv("REDIS_URL") or os.getenv("REDIS_URI")
        if redis_url:
            storage_uri = redis_url
        else:
            storage_uri = "memory://"
    limiter.init_app(app, storage_uri=storage_uri)

    # --- Caching / compression / CSRF / i18n ---------------------------------
    cache_type = app.config.get("CACHE_TYPE", "simple")  # avoid 'null' warning
    app.config["CACHE_TYPE"] = cache_type
    cache.init_app(app)
    compress.init_app(app)
    csrf.init_app(app)
    babel.init_app(app)

    # --- JWTManager (lazy import AFTER eventlet has patched) -----------------
    global jwt
    from flask_jwt_extended import JWTManager  # noqa: WPS433 (intentional local import)
    jwt = JWTManager()
    jwt.init_app(app)

    # --- Socket.IO (optionally with a message queue like Redis) --------------
    mq = app.config.get("SOCKETIO_MESSAGE_QUEUE") or os.getenv("REDIS_URL") or None
    socketio.init_app(app, message_queue=mq)


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
