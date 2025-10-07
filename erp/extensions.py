import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
login_manager = LoginManager()
mail = Mail()

# eventlet works best in this stack; gunicorn worker is set to "eventlet"
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

# Limiter 3.8 pattern: create with key_func; defaults are read from app.config
limiter = Limiter(key_func=get_remote_address)


def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Flask-Limiter: storage and defaults come from app.config (set in app.py)
    # Just init — no default_limits kwarg in 3.8+
    limiter.init_app(app)

    # SocketIO binds the Flask app
    socketio.init_app(app)
