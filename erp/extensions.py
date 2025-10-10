# erp/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_socketio import SocketIO

# Create unbound extension instances (init_app happens in create_app)
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
cors = CORS()

# If you later add Redis, set LIMITER_STORAGE_URI in config/env
limiter = Limiter(key_func=get_remote_address, enabled=True)

login_manager = LoginManager()

# Keep async_mode="eventlet" to match gunicorn worker class
socketio = SocketIO(
    async_mode="eventlet",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)
