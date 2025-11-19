# -*- coding: utf-8 -*-
from __future__ import annotations

import functools
from typing import Callable, Iterable
from flask import current_app, request, jsonify
from werkzeug.exceptions import Unauthorized, Forbidden
from sqlalchemy import select

from erp.extensions import db
from erp.models import Role, UserRoleAssignment

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

_DEFAULT_PERMISSION_MATRIX = {
    "employee": {"view:dashboard", "order:view", "order:create"},
    "client": {"view:dashboard", "order:view"},
    "finance": {"view:dashboard", "finance:read", "finance:post"},
    "admin": {"*"},
}


def _permission_matrix() -> dict[str, set[str]]:
    config_matrix = current_app.config.get("ROLE_PERMISSION_MATRIX")
    matrix = config_matrix or _DEFAULT_PERMISSION_MATRIX
    return {role: set(perms) for role, perms in matrix.items()}


def _roles_for_identity(identity: dict | None) -> set[str]:
    if not identity:
        return set()

    if "roles" in identity:
        roles = identity["roles"]
        if isinstance(roles, str):
            return {roles}
        return {str(r) for r in roles}

    if identity.get("role"):
        return {str(identity["role"])}

    user_id = identity.get("id")
    if not user_id:
        return set()

    cache_key = f"erp_roles::{user_id}"
    if cache_key in request.environ:
        return request.environ[cache_key]

    rows: Iterable[str] = db.session.execute(
        select(Role.name)
        .join(UserRoleAssignment, Role.id == UserRoleAssignment.role_id)
        .where(UserRoleAssignment.user_id == user_id)
    ).scalars().all()
    resolved = {r for r in rows if r}
    request.environ[cache_key] = resolved
    return resolved


def _is_allowed(role: str, permission: str, matrix: dict[str, set[str]]) -> bool:
    perms = matrix.get(role, set())
    return "*" in perms or permission in perms


def require_permission(permission: str) -> Callable:
    """Decorator that enforces the configured RBAC matrix."""

    def wrapper(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            ident = get_identity()
            if not ident:
                raise Unauthorized()

            roles = _roles_for_identity(ident)
            if not roles:
                raise Forbidden()

            matrix = _permission_matrix()
            if not any(_is_allowed(role, permission, matrix) for role in roles):
                raise Forbidden()

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
