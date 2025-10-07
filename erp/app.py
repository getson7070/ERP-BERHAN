from __future__ import annotations

import os
import re
from flask import Flask, render_template
from flask_cors import CORS

from .extensions import (
    db, migrate, cache, mail, login_manager, socketio, init_extensions, limiter  # noqa: F401
)
from .routes.auth import auth_bp  # make sure this exists & is named auth_bp


def _parse_limits_env(val: str | None):
    """
    Accepts: "300 per minute; 30 per second" or "300/min,30/second"
    Returns: ["300 per minute", "30 per second"]  or None
    Rejects bracketed Python-list strings to avoid parser errors.
    """
    if not val:
        return None
    if val.strip().startswith("[") and val.strip().endswith("]"):
        # It's a literal Python list string – don't pass this through.
        # Ask the operator to set "300 per minute;30 per second" instead.
        # We’ll still try to salvage it by stripping brackets and quotes:
        cleaned = val.strip().strip("[]").replace("'", "").replace('"', "")
        parts = [p.strip() for p in re.split(r"[;,]+", cleaned) if p.strip()]
        return parts or None
    parts = [p.strip() for p in re.split(r"[;,]+", val) if p.strip()]
    return parts or None


def _make_config() -> dict:
    return {
        # Flask basics
        "SECRET_KEY": os.environ.get("FLASK_SECRET_KEY", "dev-not-secret"),

        # Database
        "SQLALCHEMY_DATABASE_URI": os.environ.get("SQLALCHEMY_DATABASE_URI"),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,

        # Cache
        "CACHE_TYPE": os.environ.get("CACHE_TYPE", "SimpleCache"),
        "CACHE_DEFAULT_TIMEOUT": int(os.environ.get("CACHE_DEFAULT_TIMEOUT", "300")),

        # CORS
        "CORS_ORIGINS": os.environ.get("CORS_ORIGINS", "*"),

        # Rate limits
        "RATELIMIT_STORAGE_URI": os.environ.get("RATELIMIT_STORAGE_URI", os.environ.get("FLASK_LIMITER_STORAGE_URI", "memory://")),
        "RATELIMIT_DEFAULT": _parse_limits_env(os.environ.get("DEFAULT_RATE_LIMITS")),

        # Startup page (template)
        "ENTRY_TEMPLATE": os.environ.get("ENTRY_TEMPLATE", "choose_login.html"),

        # Optional mail settings (used elsewhere in your app)
        "MAIL_SERVER": os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
        "MAIL_PORT": int(os.environ.get("MAIL_PORT", "587")),
        "MAIL_USE_TLS": os.environ.get("MAIL_USE_TLS", "true").lower() == "true",
        "MAIL_USE_SSL": os.environ.get("MAIL_USE_SSL", "false").lower() == "true",
        "MAIL_USERNAME": os.environ.get("MAIL_USERNAME"),
        "MAIL_PASSWORD": os.environ.get("MAIL_PASSWORD"),
        "MAIL_DEFAULT_SENDER": os.environ.get("MAIL_DEFAULT_SENDER"),
    }


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(_make_config())

    # CORS
    CORS(app, resources={r"/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    # Extensions (db, mail, socketio, limiter, login_manager, etc.)
    init_extensions(app)

    # Blueprints
    app.register_blueprint(auth_bp)

    # Routes
    @app.route("/", strict_slashes=False)
    def index():
        # Render whatever ENTRY_TEMPLATE points to (choose_login.html by default)
        return render_template(app.config.get("ENTRY_TEMPLATE", "choose_login.html"))

    @app.route("/choose_login", strict_slashes=False)
    def choose_login():
        return render_template("choose_login.html")

    @app.route("/health", strict_slashes=False)
    def health():
        return "ok"

    return app
