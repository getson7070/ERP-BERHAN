import os
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

db = SQLAlchemy()
socketio = SocketIO(async_mode="threading")  # no message_queue needed

def init_extensions(app):
    db.init_app(app)
    socketio.init_app(app)  # keep defaults; won’t touch Redis
