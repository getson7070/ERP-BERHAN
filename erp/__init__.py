# erp/__init__.py
import os
from flask import Flask
from .extensions import db, migrate, csrf, login_manager
from .routes.main import main_bp
from .routes.auth import auth_bp

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # ---- Config (keep/merge your existing config) ----
    app.config.setdefault("SECRET_KEY", "change-me-in-prod")
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", os.getenv("DATABASE_URL", "sqlite:///app.db"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # ---- Init extensions ----
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    @app.context_processor
    def inject_csrf():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    # ---- Blueprints ----
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # ---- Import your models so Alembic sees them ----
    # (adjust paths if your models live elsewhere)
    try:
        from . import models  # noqa: F401
    except Exception:
        # If models are spread across modules, import them individually here.
        pass

    return app
