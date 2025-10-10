# erp/__init__.py
from __future__ import annotations

import os
from datetime import datetime
from typing import Dict

from flask import Flask, render_template, request
from .security import read_device_id, compute_activation_for_device

# Import shared extensions (instances only; no heavy app logic here)
# Your erp/extensions.py must define these objects.
from .extensions import (
    db,
    migrate,
    csrf,
    login_manager,
    limiter,
    cache,
    mail,
    socketio,
)
try:
    # CORS is optional; only init if present to avoid ImportError mismatches.
    from .extensions import cors  # type: ignore
except Exception:  # pragma: no cover
    cors = None  # type: ignore


def create_app() -> Flask:
    """Application factory used by wsgi and tests."""
    app = Flask(__name__, instance_relative_config=False)

    # ---- Base configuration (Render env already provides these) ----
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_TIME_LIMIT"] = None

    # ---- Init extensions ----
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    if cors is not None:
        # Respect CORS_ORIGINS if provided
        from flask_cors import CORS  # type: ignore
        origins = os.getenv("CORS_ORIGINS", "*")
        CORS(app, resources={r"/*": {"origins": origins}})

    # Socket.IO (Eventlet worker on Render)
    socketio.init_app(app, cors_allowed_origins="*")

    # ---- Blueprints ----
    from .routes.main import main_bp
    from .routes.auth import bp as auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # ---- Flask-Login loader (prevents “Missing user_loader” error) ----
    from .models import User  # local import to avoid circulars

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    login_manager.login_view = "auth.login"

    # ---- Template context (for header/footer, year, and UI activation switches) ----
    @app.context_processor
    def inject_globals():
        # Resolve device and activation *per request* so the landing page can toggle tiles.
        device_id = read_device_id(request)
        activation: Dict[str, bool] = compute_activation_for_device(device_id)

        return dict(
            current_year=datetime.utcnow().year,
            ui_activation=activation,
            brand_name="Berhan Pharma",
            brand_logo_url="/static/pictures/BERHAN-PHARMA-LOGO.jpg",
        )

    # ---- Error pages ----
    @app.errorhandler(404)
    def not_found(_):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_):
        # Keep this tiny and template-only (don’t call url_for with bad endpoints)
        return render_template("errors/500.html"), 500

    return app
