"""Flask application factory for ERP-BERHAN."""

import os
from flask import Flask

from .extensions import db, migrate, socketio, csrf, limiter, mail
# Keep api blueprint simple/minimal to avoid import errors
from .routes.api import api_bp


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # Basic config – keep flexible, don’t hard-fail if env is missing
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", os.getenv("DATABASE_URL", "sqlite:///app.db"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "change-me"))

    register_extensions(app)
    register_blueprints(app)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


def register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    mail.init_app(app)


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(api_bp, url_prefix="/api")
