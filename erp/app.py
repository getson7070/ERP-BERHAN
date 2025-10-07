# erp/app.py
import os
from flask import Flask, render_template
from flask_cors import CORS

from .extensions import init_extensions, limiter

# Blueprints — change/remove these imports if a module doesn't exist in your repo
from .routes.main import bp as main_bp         # public pages
from .routes.auth import auth_bp               # auth/login/logout
from .routes.api import api_bp                 # REST API (if you have it)


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # Minimal safe defaults; Render env vars override these
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "dev"))
    app.config.setdefault("ENTRY_TEMPLATE", os.getenv("ENTRY_TEMPLATE", "choose_login.html"))

    # CORS
    CORS(app, supports_credentials=True)

    # Extensions (db, migrate, cache, login, mail, limiter, socketio…)
    init_extensions(app)

    # Blueprints (only register ones that exist in your codebase)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp,  url_prefix="/api")

    # Landing page → choose login
    @app.route("/")
    def index():
        return render_template(app.config.get("ENTRY_TEMPLATE", "choose_login.html"))

    # Health endpoint (no rate limit)
    @app.get("/health")
    def health():
        return "ok", 200

    limiter.exempt(health)

    return app
