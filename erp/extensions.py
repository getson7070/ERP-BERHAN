from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

# Core extensions (created once, bound in init_extensions)
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
login_manager = LoginManager()
mail = Mail()

# Flask-Limiter 3.x: default limits come from app.config["RATELIMIT_DEFAULT"]
# Example: "300 per minute;30 per second" or ["300 per minute", "30 per second"]
limiter = Limiter(key_func=get_remote_address)

# Socket.IO (eventlet)
socketio = SocketIO(async_mode="eventlet", logger=False, engineio_logger=False)


def init_extensions(app):
    """Bind all extensions to the Flask app."""
    # Database & migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # Cache
    cache.init_app(app)

    # Mail
    mail.init_app(app)

    # Login
    login_manager.login_view = "auth.login"
    login_manager.refresh_view = "auth.login"
    login_manager.init_app(app)

    # REQUIRED: Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id: str):
        # Deferred import avoids circular imports
        from .models import User
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    # Rate limiting
    # In v3.x, defaults are read from app.config and applied automatically
    # when init_app is called.
    limiter.init_app(app)

    # Socket.IO
    socketio.init_app(
        app,
        cors_allowed_origins=app.config.get("CORS_ORIGINS", "*"),
        message_queue=app.config.get("SOCKETIO_MESSAGE_QUEUE"),
    )
