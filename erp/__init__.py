# erp/__init__.py
import os

from flask import Flask, render_template
from .extensions import db, migrate, csrf, login_manager

def _normalize_db_url(url: str | None) -> str | None:
    if not url:
        return None
    # Render often provides postgres://; SQLAlchemy 2.x wants postgresql+psycopg2://
    return url.replace("postgres://", "postgresql+psycopg2://", 1) if url.startswith("postgres://") else url

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # ---- Secrets (set on Render dashboard) ----
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me")
    app.config["WTF_CSRF_SECRET_KEY"] = os.environ.get("WTF_CSRF_SECRET_KEY", app.config["SECRET_KEY"])

    # ---- Database ----
    db_url = (
        os.environ.get("SQLALCHEMY_DATABASE_URI") or
        os.environ.get("DATABASE_URL")
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = _normalize_db_url(db_url) or "sqlite:///local.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ---- Extensions ----
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    # ---- Blueprints ----
    from .routes.main import main as main_bp
    app.register_blueprint(main_bp)
    # If you have auth/api/etc blueprints, register them here too.

    # ---- Error pages (keep endpoints blueprint-qualified) ----
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app
