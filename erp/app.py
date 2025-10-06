# erp/app.py
import os
from flask import Flask, redirect, url_for
from .extensions import db, migrate, cache, limiter, login_manager, mail, socketio, init_extensions
from .routes.auth import auth_bp
from .web import web_bp
from .models import User

def create_app(config_name=None):
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="templates",
        static_folder="static",
    )

    # Base config
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev")

    db_url = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("Set SQLALCHEMY_DATABASE_URI or DATABASE_URL")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Mail (Gmail/SMTP via env)
    app.config.setdefault("MAIL_SERVER", os.getenv("MAIL_SERVER", "localhost"))
    app.config.setdefault("MAIL_PORT", int(os.getenv("MAIL_PORT", "25")))
    app.config.setdefault("MAIL_USE_TLS", os.getenv("MAIL_USE_TLS", "false").lower() == "true")
    app.config.setdefault("MAIL_USE_SSL", os.getenv("MAIL_USE_SSL", "false").lower() == "true")
    app.config.setdefault("MAIL_USERNAME", os.getenv("MAIL_USERNAME"))
    app.config.setdefault("MAIL_PASSWORD", os.getenv("MAIL_PASSWORD"))
    app.config.setdefault("MAIL_DEFAULT_SENDER", os.getenv("MAIL_DEFAULT_SENDER"))

    # Init extensions
    init_extensions(app)

    # User loader
    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # Blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Root redirect
    @app.route("/")
    def index():
        return redirect(url_for("web.login_page"))

    # Health
    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app
