# erp/__init__.py
from flask import Flask
from .extensions import init_extensions, register_safety_login_loader, register_common_blueprints

def create_app() -> Flask:
    # Point to the package-local templates/static (this fixes TemplateNotFound)
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # SECRET_KEY must be set via env in Render; this fallback is only for dev
    app.config.setdefault("SECRET_KEY", "CHANGE_ME_IN_PROD")

    # Init extensions (db, migrate, login, limiter, cache, mail, socketio, cors, etc.)
    init_extensions(app)

    # Ensure Flask-Login never crashes on anonymous pages
    register_safety_login_loader()

    # Register ALL blueprints needed for the UI
    register_common_blueprints(app)

    return app
