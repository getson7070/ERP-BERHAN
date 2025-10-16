from __future__ import annotations
from flask import Flask
from .extensions import db, migrate
from .config import BaseConfig

def create_app(config_object: str | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(BaseConfig)

    db.init_app(app)
    migrate.init_app(app, db)

    from .views.main import bp as main_bp
    app.register_blueprint(main_bp)
    return app
