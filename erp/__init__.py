# erp/__init__.py
import os
from flask import Flask
from .extensions import db, migrate, csrf, login_manager

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # ---- Core config (merge with yours as needed) ----
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "change-me-in-prod"))
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", os.getenv("DATABASE_URL", "sqlite:///app.db"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # ---- Init extensions ----
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Required by Flask-Login even if you return None.
    @login_manager.user_loader
    def load_user(user_id):
        # If/when you add a real User model:
        # from .models import User
        # return db.session.get(User, int(user_id))
        return None

    # Make csrf_token() available in Jinja
    @app.context_processor
    def inject_csrf():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    # ---- Blueprints ----
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # If you already have models, import them so Alembic sees metadata
    try:
        from . import models  # noqa: F401
    except Exception:
        pass

    return app
