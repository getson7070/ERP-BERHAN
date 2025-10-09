import os
from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader
from .extensions import init_extensions, register_safety_login_loader, register_common_blueprints

# Resolve absolute paths for both possible template locations
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERP_DIR = os.path.join(BASE_DIR, "erp")
ERP_TEMPLATES = os.path.join(ERP_DIR, "templates")
ROOT_TEMPLATES = os.path.join(BASE_DIR, "templates")

ERP_STATIC = os.path.join(ERP_DIR, "static")
ROOT_STATIC = os.path.join(BASE_DIR, "static")

def create_app() -> Flask:
    # Primary: use package-local templates/static inside erp/
    app = Flask(
        __name__,
        template_folder="templates",  # relative to the erp package
        static_folder="static"
    )

    # Minimal config; set SECRET_KEY in Render env for production
    app.config.setdefault("SECRET_KEY", "CHANGE_ME_IN_PROD")

    # Make template discovery robust: search erp/templates first, then root/templates (if present)
    loaders = []
    if os.path.isdir(ERP_TEMPLATES):
        loaders.append(FileSystemLoader(ERP_TEMPLATES))
    if os.path.isdir(ROOT_TEMPLATES):
        loaders.append(FileSystemLoader(ROOT_TEMPLATES))
    if loaders:
        app.jinja_loader = ChoiceLoader(loaders)

    # Serve static from erp/static by default; optionally expose root/static if you have it
    # (Flask only takes one static_folder; if you need both, serve root/static via a blueprint.)

    # Init extensions early (db, migrate, login, limiter, cache, mail, cors, socketio)
    init_extensions(app)

    # Ensure anonymous pages never crash when templates touch current_user
    register_safety_login_loader()

    # Public/common blueprints
    register_common_blueprints(app)

    return app
