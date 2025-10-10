# erp/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
cache = Cache(config={"CACHE_TYPE": "SimpleCache"})
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour"])
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")
