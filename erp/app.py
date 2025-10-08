# erp/app.py
import os
from flask import Flask, render_template, redirect, url_for
from flask_cors import CORS

from erp.extensions import init_extensions, limiter


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # Load config from env first; instance/config.py is optional.
    app.config.from_mapping(
        ENTRY_TEMPLATE=os.getenv("ENTRY_TEMPLATE", "choose_login.html"),
    )
    # Instance folder may not exist in containers.
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Cross-origin (if you have a separate frontend)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Initialize extensions (db, migrate, login, limiter, cache, mail, csrf, socketio)
    init_extensions(app)

    # ---- Blueprints ----
    from erp.routes.main import bp as main_bp
    from erp.routes.auth import auth_bp
    from erp.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp, url_prefix="/api")

    # ---- Index & health ----
    @app.route("/")
    @limiter.exempt  # no need to rate limit your root/health
    def index():
        return render_template(app.config.get("ENTRY_TEMPLATE", "choose_login.html"))

    @app.get("/health")
    @limiter.exempt
    def health():
        return {"status": "ok"}

    # ---- Error Pages (optional nicer UX) ----
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app
