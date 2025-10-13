# erp/extensions.py
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_caching import Cache
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
cache = Cache()
cors = CORS()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

def _ratelimit_storage_uri() -> str:
    uri = os.getenv("RATELIMIT_STORAGE_URI")
    if uri:
        return uri
    redis_url = os.getenv("REDIS_URL") or os.getenv("REDIS_TLS_URL")
    if not redis_url:
        host = os.getenv("REDIS_HOST")
        if host:
            port = os.getenv("REDIS_PORT", "6379")
            pw = os.getenv("REDIS_PASSWORD", "")
            auth = f":{pw}@" if pw else ""
            redis_url = f"redis://{auth}{host}:{port}/0"
    return redis_url or "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_ratelimit_storage_uri(),
    strategy="moving-window",
    default_limits=["600 per minute"],
)

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    cache.init_app(app, config={"CACHE_TYPE": "simple"})
    cors.init_app(app, resources={r"/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Socket.IO with optional Redis message queue for scale
    msg_q = app.config.get("SOCKETIO_MESSAGE_QUEUE")
    socketio.init_app(app, message_queue=msg_q, cors_allowed_origins=app.config.get("CORS_ORIGINS", "*"))

    # Ensure a user_loader exists so anonymous pages don't error
    @login_manager.user_loader
    def load_user(user_id):
        try:
            from erp.models import User  # local import avoids circulars
            return db.session.get(User, int(user_id))
        except Exception:
            return None
