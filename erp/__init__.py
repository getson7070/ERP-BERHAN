# erp/__init__.py
import os
from flask import Flask, render_template
from .extensions import db, migrate, csrf, login_manager, cache, limiter, socketio

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # ---- Config ----
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
    # Render provides DATABASE_URL; SQLAlchemy expects postgresql+psycopg2://
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///local.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ---- Init extensions ----
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app)

    # ---- Blueprints ----
    from .routes.main import bp as main_bp
    from .routes.auth import bp as auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # ---- Error pages ----
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/500.html"), 500

    return app
