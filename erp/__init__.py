# erp/__init__.py
import os
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from .extensions import db, migrate, csrf, login_manager
from .routes.main import main as main_bp

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # ---- Config (ensure these are set on Render) ----
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me")
    app.config["WTF_CSRF_SECRET_KEY"] = os.environ.get(
        "WTF_CSRF_SECRET_KEY", app.config["SECRET_KEY"]
    )

    # ---- Extensions ----
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    # ---- Blueprints ----
    app.register_blueprint(main_bp)

    # ---- Error pages ----
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app
