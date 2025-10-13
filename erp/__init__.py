# erp/__init__.py
from __future__ import annotations

import importlib
import logging
import os
from datetime import datetime

from flask import Flask, render_template
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix

from erp.extensions import db  # existing SQLAlchemy instance
from erp.models import User  # existing model

login_manager = LoginManager()
login_manager.login_view = "main.choose_login"

_BLUEPRINTS = [
    "erp.routes.main:bp",
    "erp.routes.auth:bp",
]

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # ---- Core config (keeps your existing env keys) -------------------------
    app.config.from_object(os.getenv("FLASK_CONFIG", "erp.config.ProductionConfig"))
    app.config.setdefault("BRAND_NAME", "BERHAN")
    app.config.setdefault("BRAND_PRIMARY", "#0f773e")  # green
    app.config.setdefault("AUTHORIZED_DEVICES", "Xiaomi Pad 6")  # comma-separated

    # ---- DB / Login ---------------------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # ---- Context available to all templates --------------------------------
    @app.context_processor
    def inject_globals():
        return dict(
            brand_name=app.config.get("BRAND_NAME", "BERHAN"),
            brand_primary=app.config.get("BRAND_PRIMARY", "#0f773e"),
            year=datetime.utcnow().year,
        )

    # ---- Error pages --------------------------------------------------------
    @app.errorhandler(404)
    def not_found(_):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_):
        # Keep generic UI but no recursion into crashing context
        return render_template("errors/500.html"), 500

    # ---- Blueprints (stable ones only) -------------------------------------
    log = logging.getLogger("erp")
    for spec in _BLUEPRINTS:
        mod_name, attr = spec.split(":")
        try:
            mod = importlib.import_module(mod_name)
            app.register_blueprint(getattr(mod, attr))
        except Exception as exc:
            log.warning("Skipped blueprint %s due to error: %s", spec, exc)

    return app
