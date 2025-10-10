# erp/__init__.py
import os
from flask import Flask, render_template
from .extensions import db, migrate, csrf, login_manager
from .routes.main import main as main_bp

def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    # ---- Core config ----
    # Render sets DATABASE_URL; Flask-SQLAlchemy expects SQLALCHEMY_DATABASE_URI
    db_url = os.environ.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL")
    if not db_url:
        # Fallback to sqlite so alembic env can at least import without exploding.
        db_url = "sqlite:///instance/app.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # CSRF/Session secrets
    secret = os.environ.get("SECRET_KEY", "change-me")
    app.config["SECRET_KEY"] = secret
    app.config["WTF_CSRF_SECRET_KEY"] = os.environ.get("WTF_CSRF_SECRET_KEY", secret)

    # ---- Extensions ----
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # ---- Blueprints ----
    app.register_blueprint(main_bp)

    # ---- Error pages ----
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # ---- Flask-Login user loader (avoid “Missing user_loader”) ----
    # Adjust import path to your actual User model.
    from erp.models import User  # make sure this exists

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    return app
