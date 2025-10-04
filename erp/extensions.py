from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

socketio = SocketIO(cors_allowed_origins="*")
db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
