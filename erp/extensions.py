# erp/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_mail import Mail
from flask_limiter import Limiter
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
mail = Mail()

# Limiter 3.x constructor; storage defaults to in-memory unless configured
limiter = Limiter(key_func=lambda: "global")

# Eventlet-friendly
socketio = SocketIO(async_mode="eventlet")
