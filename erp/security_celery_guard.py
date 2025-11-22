"""Celery task base that enforces Phase-2 RBAC permissions."""

from __future__ import annotations

from celery import Task

from erp.models import User
from erp.security_rbac_phase2 import is_allowed
from erp.utils import resolve_org_id


class RBACGuardedTask(Task):
    abstract = True
    required_permission: tuple[str, str] | None = None

    def __call__(self, *args, **kwargs):  # type: ignore[override]
        if self.required_permission:
            resource, action = self.required_permission
            org_id = kwargs.get("org_id") or resolve_org_id()
            actor_id = kwargs.get("actor_id")
            from erp.security import _get_user_role_names

            user = User.query.filter_by(org_id=org_id, id=actor_id).first()
            roles = _get_user_role_names(user) if user else set()

            if not is_allowed(org_id, roles, resource, action, {"user_id": actor_id}):
                raise PermissionError(f"Permission denied for {resource}:{action}")

        return super().__call__(*args, **kwargs)


__all__ = ["RBACGuardedTask"]
