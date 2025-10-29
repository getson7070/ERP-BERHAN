# erp/utils/blueprints_guard.py
from __future__ import annotations
from flask import Flask, Blueprint

def install_blueprint_guard(app: Flask) -> None:
    """Prevent duplicate blueprint registration and log helpful messages."""
    seen = set()

    orig_register = app.register_blueprint

    def safe_register(blueprint: Blueprint, **kwargs):
        key = (blueprint.name, kwargs.get("url_prefix"))
        if key in seen:
            app.logger.warning("Skipping duplicate blueprint: %s (prefix=%s)", *key)
            return
        seen.add(key)
        return orig_register(blueprint, **kwargs)

    app.register_blueprint = safe_register  # type: ignore[attr-defined]
