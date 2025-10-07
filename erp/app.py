# erp/app.py
import os
from flask import Flask, render_template
from flask_cors import CORS

# only pull in the initializer to avoid circular imports
from .extensions import init_extensions

# blueprints (adjust these imports if a file/blueprint is missing)
from .routes.auth import auth_bp
from .routes.api import api_bp
from .routes.main import bp as main_bp  # public/site pages


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # Minimal safe defaults; your Render env vars can override these
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "dev"))
    app.config.setdefault("ENTRY_TEMPLATE", os.getenv("ENTRY_TEMPLATE", "choose_login.html"))
    # Example limiter defaults if you don’t set them via env:
    app.config.setdefault("RATELIMIT_DEFAULT", os.getenv("DEFAULT_RATE_LIMITS", "300 per minute;30 per second"))

    # CORS
    CORS(app, supports_credentials=True)

    # init db, login_manager, cache, mail, socketio, limiter, etc.
    init_extensions(app)

    # register blueprints
    app.register_blueprint(main_bp)                 # e.g. “/” routes
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp,  url_prefix="/api")

    # simple index → choose login
    @app.route("/")
    def index():
        return render_template(app.config.get("ENTRY_TEMPLATE", "choose_login.html"))

    # health (plain text) + no rate limit
    @app.get("/health")
    def health():
        return "ok", 200

    # Exempt health from rate limit without importing limiter at module top
    from .extensions import limiter
    limiter.exempt(health)

    return app
