from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO(async_mode="eventlet")
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200/min"])
login_manager = LoginManager()
