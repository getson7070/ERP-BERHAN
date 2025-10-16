import os
from flask import Flask
from .extensions import db

def create_app(config_object: str | None = None) -> Flask:
    app = Flask(__name__)

    # Accept a config class path string, or fall back to FLASK_CONFIG env
    config_object = config_object or os.getenv("FLASK_CONFIG", "erp.config.ProductionConfig")
    app.config.from_object(config_object)

    # init extensions
    db.init_app(app)

    # import parts of the app that register models/blueprints
    # (keep these inside the function to avoid side-effects on import)
    try:
        from . import models  # if you have a central models.py
    except Exception:
        pass

    return app
