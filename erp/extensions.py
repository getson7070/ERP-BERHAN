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
# objects that eventlet may try to traverse during monkey_patch. We import it
# lazily in init_extensions() after patching has happened.

# Core
db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()

# Limiter (configure storage via app.config in init_extensions)
limiter = Limiter(key_func=get_remote_address)

# CORS
cors = CORS()

# Optional extras
cache = Cache()          # configured in init_extensions
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
        storage_uri = os.getenv("RATELIMIT_STORAGE_URI") or os.getenv("REDIS_URL") or "memory://"
    # In Flask-Limiter 3.x, configure via app.config then call init_app(app)
    app.config["RATELIMIT_STORAGE_URI"] = storage_uri
    limiter.init_app(app)

    # --- Caching / compression / CSRF / i18n ---------------------------------
    # Coerce null/empty values to "simple" to avoid warnings
    cache_type = app.config.get("CACHE_TYPE", os.getenv("CACHE_TYPE", "simple"))
    if not cache_type or str(cache_type).lower() in {"none", "null"}:
        cache_type = "simple"
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
    mq = app.config.get("SOCKETIO_MESSAGE_QUEUE") or os.getenv("SOCKETIO_MESSAGE_QUEUE") or os.getenv("REDIS_URL")
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
