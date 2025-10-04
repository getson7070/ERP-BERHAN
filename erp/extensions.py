from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

socketio = SocketIO(cors_allowed_origins="*")
db = SQLAlchemy()
migrate = Migrate()
