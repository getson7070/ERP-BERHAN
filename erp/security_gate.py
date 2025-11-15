# -*- coding: utf-8 -*-
from __future__ import annotations

import functools
from typing import Callable
from flask import current_app, request, jsonify
from werkzeug.exceptions import Unauthorized, Forbidden

# Mark API endpoints that should be CSRF-exempt but JWT-required.
API_CSRF_EXEMPT_PREFIXES = (
    "/api/",          # REST API
    "/bot/",          # Telegram/WhatsApp hooks
    "/webhook/",      # generic webhooks
)

def is_machine_endpoint(path: str) -> bool:
    return any(path.startswith(pfx) for pfx in API_CSRF_EXEMPT_PREFIXES)

def get_identity():
    """
    Replace with your real identity retrieval logic:
      - flask_login current_user
      - flask_jwt_extended get_jwt()
      - session, etc.
    """
    user = getattr(request, "user", None)
    if user:
        return {"id": getattr(user, "id", None), "role": getattr(user, "role", None)}
    # If using JWT, e.g.:
    try:
        from flask_jwt_extended import get_jwt, verify_jwt_in_request
        verify_jwt_in_request(optional=True)
        claims = get_jwt() or {}
        if claims:
            return {"id": claims.get("sub"), "role": claims.get("role")}
    except Exception:
        pass
    return None

def require_permission(permission: str) -> Callable:
    """
    Decorator for fine-grained checks (fill out the matrix later).
    """
    def wrapper(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            ident = get_identity()
            if not ident:
                raise Unauthorized()
            # TODO: implement your permission matrix
            # if not permissions_service.allowed(ident["role"], permission):
            #     raise Forbidden()
            return fn(*args, **kwargs)
        return inner
    return wrapper

def install_global_gate(app):
    """
    Global before_request hook:
      - Machine endpoints: require JWT, exempt CSRF (handled by your CSRF extension config)
      - Human endpoints: require session-based auth (customize as needed)
    """
    @app.before_request
    def _gate():
        path = request.path or "/"
        if is_machine_endpoint(path):
            # Require JWT
            ident = get_identity()
            if not ident:
                # Return 401 JSON for API clients
                return jsonify({"error": "auth_required"}), 401
            # CSRF exemption for machine endpoints is handled by not using forms; if you added a CSRF extension,
            # you can also register explicit exemptions via csrf.exempt in your API blueprints.
            return  # allow
        else:
            # Human pages: ensure there is some identity (session/cookie based)
            ident = get_identity()
            if not ident:
                # Let your login manager redirect; fallback to 401
                raise Unauthorized()
