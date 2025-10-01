import os
from flask import Flask, jsonify, redirect, url_for
from werkzeug.routing import BuildError

from .extensions import (
    db,
    migrate,
    oauth,
    limiter,
    cors,
    cache,
    compress,
    csrf,
    babel,
    jwt,
    socketio,
    init_extensions,
)


def _load_default_config(app: Flask) -> None:
    """Reasonable defaults; env overrides win."""
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "change-me"))
    app.config.setdefault(
        "SQLALCHEMY_DATABASE_URI", os.environ.get("DATABASE_URL", "sqlite:///app.db")
    )
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Limiter
    app.config.setdefault("RATELIMIT_DEFAULT", "100/minute")

    # CORS
    app.config.setdefault("CORS_ORIGINS", os.environ.get("CORS_ORIGINS", "*"))

    # Flask-Caching (simple in-memory by default)
    app.config.setdefault("CACHE_TYPE", os.environ.get("CACHE_TYPE", "SimpleCache"))
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", 300)

    # Socket.IO message queue (optional)
    # e.g. redis://:password@hostname:6379/0
    if "SOCKETIO_MESSAGE_QUEUE" not in app.config:
        mq = os.environ.get("SOCKETIO_MESSAGE_QUEUE")
        if mq:
            app.config["SOCKETIO_MESSAGE_QUEUE"] = mq


def create_app(config_object: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    _load_default_config(app)
    if config_object:
        app.config.from_object(config_object)

    # Initialize all extensions in one place
    init_extensions(app)

    # --- Routes --------------------------------------------------------------

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    @app.route("/", methods=["GET", "HEAD"])
    def _root():
        """
        Redirect to an auth page if available; otherwise a safe fallback.
        Your logs showed 'auth.choose_login' doesn't exist; 'auth.login' does.
        """
        for endpoint in ("auth.choose_login", "auth.login", "login"):
            try:
                return redirect(url_for(endpoint))
            except BuildError:
                continue
        # Fallback that always exists
        return redirect(url_for("health"))

    # ------------------------------------------------------------------------

    return app
