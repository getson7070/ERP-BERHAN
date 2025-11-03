from .health import bp as health_bp
from __future__ import annotations
from flask import Flask
from .utils.blueprints_guard import safe_register
from .blueprints_explicit import EXPLICIT_BLUEPRINTS
from .blueprints.compat_ext import extend_blueprints

def _register_blueprints(app: Flask, pairs):
    seen = set()
    for bp, prefix in pairs:
        name = getattr(bp, "name", None)
        if name in seen:
            continue
        seen.add(name)
        safe_register(app, bp, url_prefix=prefix)

def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    if config:
        app.config.update(config)
    pairs = EXPLICIT_BLUEPRINTS + extend_blueprints()
    _register_blueprints(app, pairs)
        app.register_blueprint(health_bp)
    return app
