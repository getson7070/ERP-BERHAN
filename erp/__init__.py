# erp/__init__.py
from flask import Flask

def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    if test_config:
        app.config.update(test_config)

    # Register Phase-1 health endpoints
    from .blueprints.health import bp as health_bp
    app.register_blueprint(health_bp)  # uses bp's own url_prefix if set

    return app
