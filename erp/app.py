from __future__ import annotations
import os
from pathlib import Path
from typing import List
from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader

from .extensions import db, migrate, limiter, socketio

def _configure_templates(app: Flask) -> None:
    default_loader = app.jinja_loader
    root_templates = Path(app.root_path).parent / "templates"
    loaders: List[FileSystemLoader] = []
    if root_templates.exists():
        loaders.append(FileSystemLoader(str(root_templates)))
    if default_loader and loaders:
        app.jinja_loader = ChoiceLoader([default_loader, *loaders])
    elif loaders:
        app.jinja_loader = ChoiceLoader(loaders)

def _apply_core_config(app: Flask) -> None:
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-not-secret")
    if os.getenv("APP_ENV") == "production":
        app.config["SESSION_COOKIE_SECURE"] = True

    db_uri = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL") or ""
    if not db_uri and os.getenv("APP_ENV") == "production":
        raise RuntimeError("SQLALCHEMY_DATABASE_URI (or DATABASE_URL) must be set.")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri or "sqlite:///instance/dev.db"
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault(
        "RATELIMIT_STORAGE_URI",
        os.getenv("RATELIMIT_STORAGE_URI", os.getenv("FLASK_LIMITER_STORAGE_URI", "memory://")),
    )

def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

def _register_blueprints(app: Flask) -> None:
    from .web import web_bp
    app.register_blueprint(web_bp)

def create_app() -> Flask:
    app = Flask(__name__)
    _apply_core_config(app)
    _configure_templates(app)

    @app.context_processor
    def _inject_i18n():
        return {"_": (lambda s, **kwargs: s)}

    @app.get("/health")
    def _health():
        return {"app": "ERP-BERHAN", "status": "running"}, 200

    _register_extensions(app)
    _register_blueprints(app)
    return app
