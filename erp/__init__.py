# erp/__init__.py
from __future__ import annotations

from flask import Flask
from .blueprints.health import bp as health_bp


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)
    if testing:
        app.config.update(TESTING=True)

    # Phase-1 health/readiness endpoints
    app.register_blueprint(health_bp)

    return app
