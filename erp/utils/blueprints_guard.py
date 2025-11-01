from __future__ import annotations
from flask import Blueprint
from typing import Optional
import logging

log = logging.getLogger(__name__)

def safe_register(app, blueprint: Blueprint, **kwargs) -> Optional[Blueprint]:
    name = getattr(blueprint, "name", None)
    prefix = kwargs.get("url_prefix")
    if name in app.blueprints:
        log.warning("Skipping duplicate blueprint: %s (prefix=%s)", name, prefix)
        return app.blueprints.get(name)
    try:
        app.register_blueprint(blueprint, **kwargs)
        return blueprint
    except (ValueError, AssertionError) as e:
        log.warning("Skipping blueprint '%s' due to route conflict; err=%s", name, e)
        return app.blueprints.get(name)
