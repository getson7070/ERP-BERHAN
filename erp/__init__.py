from __future__ import annotations
import os
from flask import Flask
from .extensions import init_extensions, register_blueprints

def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.getenv("TEMPLATE_FOLDER", "templates"),
        static_folder=os.getenv("STATIC_FOLDER", "static"),
    )

    # Map DATABASE_URL -> SQLALCHEMY_DATABASE_URI
    db_url = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL or SQLALCHEMY_DATABASE_URI must be set in the environment.")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url

    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "CHANGE_ME_IN_PROD"))

    init_extensions(app)
    register_blueprints(app)
    return app
