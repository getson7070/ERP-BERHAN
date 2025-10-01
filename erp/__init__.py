# erp/__init__.py
from flask import Flask
from .extensions import db, migrate, oauth, limiter, cors, init_extensions

def create_app(config_object='config.Config', **overrides):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    app.config.update(overrides)

    init_extensions(app)

    # Blueprints
    from .routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    # register other blueprints here...

    return app

__all__ = ["db", "migrate", "oauth", "limiter", "cors", "create_app"]
