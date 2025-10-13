# erp/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
mail = Mail()

# memory:// is fine for now; can be swapped to redis via env later
limiter = Limiter(key_func=get_remote_address, default_limits=[])

# eventlet is patched in wsgi.py; flask-socketio will use it automatically
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")
