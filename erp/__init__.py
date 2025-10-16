from flask import Flask
from .extensions import db, migrate

def create_app(config_object=None):
    app = Flask(__name__)
    if config_object:
        app.config.from_object(config_object)

    # defaults for local/dev
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///app.db")
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # blueprints (best-effort imports)
    try:
        from .blueprints.bots import bp as bots_bp
        app.register_blueprint(bots_bp, url_prefix="/bots")
    except Exception:
        pass
    try:
        from .blueprints.finance import bp as finance_bp
        app.register_blueprint(finance_bp, url_prefix="/finance")
    except Exception:
        pass
    try:
        from .blueprints.integration import bp as integration_bp
        app.register_blueprint(integration_bp, url_prefix="/integration")
    except Exception:
        pass
    try:
        from .blueprints.recall import bp as recall_bp
        app.register_blueprint(recall_bp, url_prefix="/recall")
    except Exception:
        pass

    return app
