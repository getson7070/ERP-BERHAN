from __future__ import annotations
import os, json, re
from typing import Dict, Callable, Any

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except Exception:  # pragma: no cover
    Limiter = None
    get_remote_address = None

_limiter: Limiter | None = None

def install_limiter(app) -> None:
    global _limiter
    if Limiter is None:
        app.logger.info("flask-limiter not installed; rate limits disabled")
        return
    storage_uri = os.environ.get("REDIS_URL") or "memory://"
    default_limits = []
    env_defaults = os.environ.get("ERP_RATE_LIMITS") or os.environ.get("PHASE1_RATE_LIMITS")
    if env_defaults:
        default_limits = [s.strip() for s in env_defaults.split(";") if s.strip()]
    _limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        storage_uri=storage_uri,
        default_limits=default_limits or None,
        headers_enabled=True,
    )
    # Apply per-blueprint mapping if provided in env (JSON: {bp_name: "10/minute;100/day"})
    mapping_raw = os.environ.get("ERP_BP_LIMITS", "")
    if mapping_raw:
        try:
            mapping = json.loads(mapping_raw)
            apply_blueprint_limits(app, mapping)
            app.logger.info("Applied blueprint limits: %s", list(mapping.keys()))
        except Exception as e:
            app.logger.warning("ERP_BP_LIMITS parse/apply failed: %s", e)

def add_limits(expr: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to apply limits on a specific view when flask-limiter is installed."""
    def _wrap(func):
        if _limiter is None:
            return func
        return _limiter.limit(expr)(func)
    return _wrap

def apply_blueprint_limits(app, mapping: Dict[str, str]) -> None:
    """Monkey-patch view functions to enforce per-blueprint limits without changing route code.

    mapping: { 'auth': '10/minute;100/day', 'login': '10/minute' }
    """
    if _limiter is None:
        return
    # Build regex for blueprint match (exact name)
    for bp_name, expr in mapping.items():
        # iterate endpoints owned by the blueprint
        for rule in list(app.url_map.iter_rules()):
            if "." not in rule.endpoint:
                continue
            ep_bp, ep_name = rule.endpoint.split(".", 1)
            if ep_bp != bp_name:
                continue
            view = app.view_functions.get(rule.endpoint)
            if view is None:
                continue
            # wrap once
            wrapped = _limiter.limit(expr)(view)
            app.view_functions[rule.endpoint] = wrapped
