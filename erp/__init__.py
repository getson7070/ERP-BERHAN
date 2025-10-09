from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .extensions import login_manager
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ---- Core config (adapt to your env) ----
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me-in-prod")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # ---- Init extensions ----
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # route endpoint name

    # ---- Models must be imported after db init ----
    from .models.user import User  # noqa: F401

    # ---- Blueprints / routes ----
    from .routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    from .routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    with app.app_context():
        # If you are on Postgres via Alembic, you can remove this create_all line.
        # It's harmless if tables already exist.
        db.create_all()

    return app
