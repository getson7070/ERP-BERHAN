"""Permission decorators built on the Phase-2 RBAC policy engine."""

from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import jsonify, redirect, request, url_for
from flask_login import current_user

from erp.security_rbac_phase2 import ensure_default_policy, is_allowed


def _is_api_request() -> bool:
    return (
        request.path.startswith("/api/")
        or request.accept_mimetypes.best == "application/json"
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


def require_permission(resource: str, action: str) -> Callable:
    """Decorator enforcing policy-based permission checks."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not getattr(current_user, "is_authenticated", False):
                if _is_api_request():
                    return jsonify({"error": "authentication_required"}), 401
                return redirect(url_for("auth.login", next=request.url))

            org_id = getattr(current_user, "org_id", None) or 1
            roles = getattr(current_user, "roles", None) or []
            actor_id = getattr(current_user, "id", None)

            ensure_default_policy(int(org_id))

            ctx = {
                "actor_id": actor_id,
                # route handlers can add more fields to ctx by setting request.rbac_ctx
            }
            extra_ctx = getattr(request, "rbac_ctx", None)
            if isinstance(extra_ctx, dict):
                ctx.update(extra_ctx)

            if not is_allowed(int(org_id), roles, resource, action, ctx):
                payload = {
                    "error": "permission_denied",
                    "resource": resource,
                    "action": action,
                }
                if _is_api_request():
                    return jsonify(payload), 403
                # For HTML requests, redirect to a safe page (or show a flash message later)
                return redirect(url_for("home.index"))

            return fn(*args, **kwargs)

        return wrapper

    return decorator
