from __future__ import annotations

import os
from typing import Any
from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader

from .extensions import db, migrate, socketio, csrf, limiter, login_manager


def _resolve_db_uri() -> str:
    # Prefer SQLALCHEMY_DATABASE_URI but accept DATABASE_URL (Render uses this)
    uri = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    if not uri:
        # Last-resort fallback to avoid crashing at boot; still logs visibly
        uri = "sqlite:///:memory:"
    return uri


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        template_folder=None,  # we’ll mount both roots via ChoiceLoader
    )

    # --- Config (safe for production defaults) ---
    app.config.setdefault("SECRET_KEY", os.getenv("FLASK_SECRET_KEY", "dev-secret"))
    app.config["SQLALCHEMY_DATABASE_URI"] = _resolve_db_uri()
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # --- Jinja: search BOTH ./templates and ./erp/templates ---
    root_templates = FileSystemLoader("templates")
    pkg_templates = FileSystemLoader("erp/templates")
    app.jinja_loader = ChoiceLoader([root_templates, pkg_templates])

    # --- Init extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, message_queue=None)  # no broker required for now

    # --- Minimal web blueprint only (no auto-import of other modules) ---
    from .web import web_bp
    app.register_blueprint(web_bp)

    # --- Jinja helpers: _() and now() prevent “_ is undefined” etc. ---
    @app.context_processor
    def _inject_helpers() -> dict[str, Any]:
        return {
            "_": (lambda s, *a, **k: s),   # no-op i18n so templates render
        }

    # Simple error pages (keep the app running even if a template is missing)
    @app.errorhandler(404)
    def _404(_e):  # noqa: D401
        return "Not Found", 404

    @app.errorhandler(500)
    def _500(_e):
        return "Internal Server Error", 500

    return app
