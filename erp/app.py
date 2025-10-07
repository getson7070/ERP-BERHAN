from __future__ import annotations

import os
import re
from flask import Flask, render_template
from flask_cors import CORS

from .extensions import (
    db, migrate, cache, limiter, login_manager, mail, socketio, init_extensions
)
from .routes.auth import auth_bp
from .routes.web import web_bp


def _parse_limits(value):
    """Accepts list/tuple or a semicolon/comma-delimited string."""
    if not value:
        return None
    if isinstance(value, (list, tuple)):
        return [str(x).strip() for x in value if str(x).strip()]
    # "300 per minute;30 per second" or "300 per minute, 30 per second"
    items = [i.strip() for i in re.split(r"[;,]+", str(value)) if i.strip()]
    return items or None


def _make_config() -> dict:
    """Build app config from env with safe defaults."""
    cfg = {
        "SECRET_KEY": os.environ.get("FLASK_SECRET_KEY", "dev-not-secret"),
        "SQLALCHEMY_DATABASE_URI": os.environ.get("SQLALCHEMY_DATABASE_URI"),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,

        # Caching
        "CACHE_TYPE": os.environ.get("CACHE_TYPE", "SimpleCache"),
        "CACHE_DEFAULT_TIMEOUT": int(os.environ.get("CACHE_DEFAULT_TIMEOUT", "300")),

        # CORS
        "CORS_ORIGINS": os.environ.get("CORS_ORIGINS", "*"),

        # Rate limiting
        "RATELIMIT_STORAGE_URI": os.environ.get("RATELIMIT_STORAGE_URI", os.environ.get("FLASK_LIMITER_STORAGE_URI", "memory://")),
        # Choose one of these envs (both supported):
        # DEFAULT_RATE_LIMITS="300 per minute;30 per second"
        # or RATELIMIT_DEFAULT with same format
        "RATELIMIT_DEFAULT": _parse_limits(
            os.environ.get("DEFAULT_RATE_LIMITS") or os.environ.get("RATELIMIT_DEFAULT")
        ),

        # Templates
        "ENTRY_TEMPLATE": os.environ.get("ENTRY_TEMPLATE", "choose_login.html"),
    }
    # Keep MAIL_* passthroughs
    for k in ("MAIL_SERVER", "MAIL_PORT", "MAIL_USERNAME", "MAIL_PASSWORD",
              "MAIL_USE_TLS", "MAIL_USE_SSL", "MAIL_DEFAULT_SENDER"):
        if os.environ.get(k) is not None:
            cfg[k] = os.environ.get(k)
    return cfg


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(_make_config())

    # CORS
    CORS(app, resources={r"/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    # Bind extensions (db, cache, mail, login_manager, limiter, socketio)
    init_extensions(app)

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)

    # Routes
    @app.route("/", strict_slashes=False)
    def index():
        # Simple landing to the chooser or whatever ENTRY_TEMPLATE is
        return render_template(app.config.get("ENTRY_TEMPLATE", "choose_login.html"))

    @app.route("/choose_login", strict_slashes=False)
    def choose_login():
        return render_template("choose_login.html")

    @app.route("/health", strict_slashes=False)
    def health():
        return "ok"

    return app
