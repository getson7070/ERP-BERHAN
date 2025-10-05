# erp/app.py
import os
from flask import Flask
from .extensions import (
    db, migrate, cache, limiter, login_manager, mail, socketio, init_extensions
)
from .web import web_bp
from .routes.auth import auth_bp
from .models import User

def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True,
                template_folder="templates", static_folder="static")

    # --- Base config ---
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev")

    db_url = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("Set SQLALCHEMY_DATABASE_URI or DATABASE_URL")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Mail (optional; safe defaults)
    app.config.setdefault("MAIL_SERVER", os.getenv("MAIL_SERVER", "localhost"))
    app.config.setdefault("MAIL_PORT", int(os.getenv("MAIL_PORT", "25")))
    app.config.setdefault("MAIL_USE_TLS", os.getenv("MAIL_USE_TLS", "false").lower() == "true")
    app.config.setdefault("MAIL_USERNAME", os.getenv("MAIL_USERNAME"))
    app.config.setdefault("MAIL_PASSWORD", os.getenv("MAIL_PASSWORD"))
    app.config.setdefault("MAIL_DEFAULT_SENDER", os.getenv("MAIL_DEFAULT_SENDER"))

    # Init all extensions (db/cache/mail/limiter/socketio/login)
    init_extensions(app)

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # Blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp)

    # Health endpoint
    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app
