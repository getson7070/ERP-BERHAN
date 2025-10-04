# erp/app.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader

# Optional: if you have extensions, import them defensively
try:
    from .extensions import db, migrate, limiter, socketio  # type: ignore
except Exception:  # keep startup resilient
    db = migrate = limiter = socketio = None  # type: ignore


def _configure_templates(app: Flask) -> None:
    """
    Make Jinja search both:
      - <repo>/templates
      - <repo>/erp/templates  (Flask's default for this package)
    """
    # existing loader (points at erp/templates by default)
    default_loader = app.jinja_loader
    # repo root is one level up from erp/ package
    repo_root = Path(app.root_path).parent
    root_templates = repo_root / "templates"

    extra_loaders: list[FileSystemLoader] = []
    if root_templates.exists():
        extra_loaders.append(FileSystemLoader(str(root_templates)))

    if default_loader and extra_loaders:
        app.jinja_loader = ChoiceLoader([default_loader, *extra_loaders])
    elif extra_loaders:
        app.jinja_loader = ChoiceLoader(extra_loaders)


def _register_extensions(app: Flask) -> None:
    if db:
        db.init_app(app)
    if migrate and db:
        migrate.init_app(app, db)
    if limiter:
        # Respect configured storage; default is memory:// (OK for now)
        limiter.init_app(app)
    if socketio:
        # eventlet worker is used; no explicit async_mode needed
        socketio.init_app(app, cors_allowed_origins="*")


def _register_blueprints(app: Flask) -> None:
    # Web/UI routes
    from .web import web_bp  # local import keeps startup lean
    app.register_blueprint(web_bp)

    # If you want to auto-register optional blueprints later, do it here
    # with try/except so missing models don’t crash startup.


def create_app() -> Flask:
    app = Flask(__name__)

    # Core config
    app.config.update(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "dev-not-secret"),
        SESSION_COOKIE_SECURE=True if os.getenv("APP_ENV") == "production" else False,
    )

    # Jinja: search both template roots
    _configure_templates(app)

    # Provide a no-op i18n function so {{ _('…') }} never crashes
    @app.context_processor
    def _inject_i18n():
        return {"_": (lambda s, **_: s)}

    # Health endpoint (kept here so app always has a live route)
    @app.get("/health")
    def _health():
        return {"app": "ERP-BERHAN", "status": "running"}, 200

    # Extensions & blueprints
    _register_extensions(app)
    _register_blueprints(app)

    return app
