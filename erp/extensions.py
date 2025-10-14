import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_mail import Mail
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
cache = Cache()
mail = Mail()

# SocketIO with eventlet-friendly setup
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

def init_limiter(app):
    storage_uri = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    limiter = Limiter(get_remote_address, storage_uri=storage_uri)
    limiter.init_app(app)
    return limiter
