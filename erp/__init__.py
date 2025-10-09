from flask import Flask
from .extensions import init_extensions, register_safety_login_loader, register_common_blueprints

def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    # Minimal, environment-driven config. SECRET_KEY must be set in env on Render.
    # Database & other configs are pulled by each extension from env where relevant.
    app.config.setdefault("SECRET_KEY", "CHANGE_ME_IN_PROD")

    # Initialize all extensions (db, migrate, login, limiter, cache, mail, socketio, cors, etc.)
    init_extensions(app)

    # Ensure Flask-Login never crashes anonymous pages even if models aren’t imported yet
    register_safety_login_loader()

    # Register only the blueprints that must be usable before auth exists
    register_common_blueprints(app)

    return app
