import os
from flask import Flask, render_template
from .extensions import db, migrate, csrf, login_manager, cache, limiter

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # --- core config (adjust as needed) ---
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me")
    app.config["WTF_CSRF_SECRET_KEY"] = os.environ.get("WTF_CSRF_SECRET_KEY", app.config["SECRET_KEY"])
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///local.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- init extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)

    # ensure models are imported so Alembic sees them
    from . import models  # noqa: F401
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    login_manager.login_view = "auth.login"

    # --- blueprints ---
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # --- health + error handlers ---
    @app.route("/health")
    def health():
        return "OK", 200

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app
