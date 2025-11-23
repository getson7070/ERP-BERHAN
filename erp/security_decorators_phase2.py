"""Permission decorators built on the Phase-2 RBAC policy engine."""

from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import jsonify, request
from flask_login import current_user

from erp.security_rbac_phase2 import is_allowed


def require_permission(resource: str, action: str) -> Callable:
    """Decorator enforcing policy-based permission checks.

    Example:
        @require_permission("inventory.stock", "adjust")
        def adjust(): ...
    """

    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from erp.security import _get_user_role_names  # local import to avoid cycle
            from erp.utils import resolve_org_id

            org_id = resolve_org_id()
            roles = _get_user_role_names(current_user) if current_user else set()
            ctx = {
                "user_id": getattr(current_user, "id", None),
                "ip": request.remote_addr,
            }

            if not is_allowed(org_id, roles, resource, action, ctx):
                return (
                    jsonify(
                        {
                            "error": "permission_denied",
                            "resource": resource,
                            "action": action,
                        }
                    ),
                    403,
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["require_permission"]
