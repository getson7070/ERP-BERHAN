# -*- coding: utf-8 -*-
from __future__ import annotations

import functools
from typing import Callable, Iterable
from flask import current_app, request, jsonify, redirect, url_for
from werkzeug.exceptions import Unauthorized, Forbidden
from sqlalchemy import select

from erp.bot_security import (
    describe_machine_identity,
    verify_slack_request,
    verify_telegram_secret,
)
from erp.extensions import db
from erp.models import Role, UserRoleAssignment

# Mark API endpoints that should be CSRF-exempt but JWT-required.
API_CSRF_EXEMPT_PREFIXES = (
    "/api/",          # REST API
    "/bot/",          # Telegram/WhatsApp hooks
    "/bots/",         # Slack blueprint + automation hooks
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

    service_identity = _service_token_identity()
    if service_identity:
        return service_identity

    machine_identity = _machine_identity_from_request()
    if machine_identity:
        return machine_identity
    return None


def _service_token_identity() -> dict | None:
    token = request.headers.get("X-Service-Token")
    if not token:
        return None
    mapping = current_app.config.get("SERVICE_TOKEN_MAP") or {}
    roles = mapping.get(token)
    if not roles:
        return None
    return {"id": f"svc:{token}", "roles": roles}


def _machine_identity_from_request() -> dict | None:
    path = request.path or "/"
    if path.startswith("/bots/slack") and verify_slack_request(request):
        return describe_machine_identity("slack:webhook")
    if path.startswith("/bot/telegram") and verify_telegram_secret(request):
        return describe_machine_identity("telegram:webhook")
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
    # Health/readiness endpoints must stay publicly accessible for load balancers and k8s probes.
    # Keep this allowlist small and path-based (no wildcards) to minimise bypass risk.
    PUBLIC_PATHS = {
        "/health",
        "/healthz",
        "/health/ready",
        "/health/live",
        "/health/readyz",
        "/healthz/ready",
        "/readyz",
        "/status",
        "/status/health",
        "/status/healthz",
        # Auth endpoints must stay reachable for unauthenticated users to sign in or self-register.
        "/auth/login",
        "/login",
        "/auth/register",
    }

    PUBLIC_PREFIXES = (
        "/static/",
        "/assets/",
        "/favicon",
        "/robots.txt",
    )

    @app.before_request
    def _gate():
        if current_app.config.get("TESTING"):
            return
        path = request.path or "/"
        if path in PUBLIC_PATHS or path.endswith("/") and path[:-1] in PUBLIC_PATHS:
            return  # allow unauthenticated probes and login/register flows
        if any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
            return  # allow unauthenticated static assets and icons
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
                if request.accept_mimetypes.accept_html and not request.is_json:
                    try:
                        login_url = url_for("auth.login", next=request.url)
                    except Exception:
                        login_url = "/auth/login"
                    return redirect(login_url)
                # Let your login manager redirect; fallback to 401 for API/non-HTML
                raise Unauthorized()
