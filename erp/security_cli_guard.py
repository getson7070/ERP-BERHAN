"""Click command wrapper to enforce RBAC policies for CLI tools."""

from __future__ import annotations

import click

from erp.models import User
from erp.security_rbac_phase2 import is_allowed


def permission_command(resource: str, action: str):
    """Decorator to guard Click commands with RBAC policies."""

    def decorator(fn):
        @click.pass_context
        def wrapper(ctx, *args, **kwargs):
            org_id = kwargs.get("org_id")
            actor_id = kwargs.get("actor_id")
            from erp.security import _get_user_role_names

            user = User.query.filter_by(org_id=org_id, id=actor_id).first()
            roles = _get_user_role_names(user) if user else set()

            if not is_allowed(org_id, roles, resource, action, {"user_id": actor_id}):
                raise click.ClickException(
                    f"Permission denied for {resource}:{action}"
                )

            return fn(ctx, *args, **kwargs)

        return click.command()(wrapper)

    return decorator


__all__ = ["permission_command"]
