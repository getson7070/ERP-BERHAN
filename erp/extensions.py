from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)  # storage set via app.config
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")
