# Application factory kept minimal to avoid importing heavy stuff too early.
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# Global extensions (but not bound to app until init_app)
db = SQLAlchemy()

# SocketIO: eventlet async mode; Redis message queue optional
socketio = SocketIO(
    async_mode="eventlet",
    cors_allowed_origins="*",
    message_queue=None  # set to your Redis URL later if you horizontally scale
)

def create_app():
    app = Flask(__name__)

    # Load config from env; don't crash if SECRET_KEY is absent in build step
    app.config["SECRET_KEY"] = app.config.get("SECRET_KEY") or \
        (os.environ.get("SECRET_KEY") or "dev-please-change-me")

    # If you have a settings object/module keep it; just don’t import modules that do work at import time
    # Example (adjust if you use a different config loader):
    # app.config.from_object("erp.settings.Config")

    # Init extensions
    db.init_app(app)
    socketio.init_app(app)

    # ---- IMPORTANT: defer Celery entirely unless explicitly enabled ----
    # We provide a toggle so Celery can be re-enabled in future without touching app boot.
    if app.config.get("ENABLE_CELERY") and app.config.get("CELERY_BROKER_URL"):
        from .celery_ext import init_celery
        init_celery(app)  # safe, context-aware
    # --------------------------------------------------------------------

    # Register your blueprints here (import lazily inside function to avoid side effects at import time)
    from .views.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Repeat for your modules (names taken from your navbar): tenders, orders, crm, hr, procurement, manufacturing, projects, plugins, privacy, status, help
    # Only example shown; keep your existing blueprints and URLs.
    # from .views.tenders import bp as tenders_bp
    # app.register_blueprint(tenders_bp, url_prefix="/tenders")

    # Health endpoint for Render
    @app.get("/status")
    def status():
        return {"ok": True}

    return app

import os  # keep after create_app to avoid masking above os usage
