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
# We deliberately DO NOT import "from flask_jwt_extended import JWTManager" here.
# Importing that module creates a LocalProxy (current_user) at import time, which
# eventlet's monkey_patch would try to traverse. We import it lazily inside
# init_extensions() *after* eventlet is patched.

# Core
db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()
limiter = Limiter(key_func=get_remote_address)
cors = CORS()

# Optional extras
cache = Cache()
compress = Compress()
csrf = CSRFProtect()
babel = Babel()

# Will be created lazily in init_extensions
jwt = None  # type: ignore[assignment]

# Realtime (eventlet backend)
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")


def init_extensions(app):
    """
    Initialize all Flask extensions with the Flask app.
    Kept centralized so erp.__init__ / erp.app can simply call this.
    """
    # Database & migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # OAuth
    oauth.init_app(app)

    # CORS & Rate limiting
    limiter.init_app(app)
    origins = app.config.get("CORS_ORIGINS", "*")
    if isinstance(origins, str) and origins != "*":
        origins = [o.strip() for o in origins.split(",") if o.strip()]
    cors.init_app(app, resources={r"/*": {"origins": origins}})

    # Caching / compression / CSRF / i18n
    cache.init_app(app)
    compress.init_app(app)
    csrf.init_app(app)
    babel.init_app(app)

    # Lazily import and init JWTManager now (AFTER eventlet monkey_patch has run)
    global jwt
    from flask_jwt_extended import JWTManager  # noqa: WPS433 (intentional local import)

    jwt = JWTManager()
    jwt.init_app(app)

    # Socket.IO (optionally with a message queue like Redis)
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
