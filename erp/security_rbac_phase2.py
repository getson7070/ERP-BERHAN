"""Policy-based RBAC evaluator (Phase-2).

The engine keeps compatibility with the existing role checks while enabling
admins to manage allow/deny rules, wildcards, and simple conditions.
"""

from __future__ import annotations

from fnmatch import fnmatch
from functools import lru_cache
from typing import Iterable

from erp.models import RBACPolicy, RBACPolicyRule, RoleHierarchy


@lru_cache(maxsize=2048)
def _load_rules(org_id: int) -> list[RBACPolicyRule]:
    policies: Iterable[RBACPolicy] = (
        RBACPolicy.query.filter_by(org_id=org_id, is_active=True)
        .order_by(RBACPolicy.priority.asc())
        .all()
    )

    rules: list[RBACPolicyRule] = []
    for policy in policies:
        rules.extend(policy.rules)
    return rules


def invalidate_policy_cache() -> None:
    """Clear cached rules after CRUD operations."""

    _load_rules.cache_clear()


def role_dominates(org_id: int, parent_role: str, child_role: str) -> bool:
    """Return True if *parent_role* outranks or equals *child_role*."""

    if parent_role == child_role:
        return True

    return (
        RoleHierarchy.query.filter_by(
            org_id=org_id, parent_role=parent_role, child_role=child_role
        ).first()
        is not None
    )


def is_allowed(
    org_id: int,
    user_roles: list[str] | set[str],
    resource: str,
    action: str,
    ctx: dict | None = None,
) -> bool:
    """Evaluate allow/deny rules for a user.

    Deny wins over allow. Wildcards are supported on resource and action.
    """

    ctx = ctx or {}
    rules = _load_rules(org_id)

    matched_allow = False

    for rule in rules:
        if rule.role_key not in user_roles:
            continue

        if not fnmatch(resource, rule.resource):
            continue
        if not fnmatch(action, rule.action):
            continue

        if not _conditions_met(rule.condition_json or {}, ctx):
            continue

        if rule.effect == "deny":
            return False
        if rule.effect == "allow":
            matched_allow = True

    return matched_allow


def _conditions_met(conditions: dict, ctx: dict) -> bool:
    """Minimal condition evaluator; extendable without schema changes."""

    if not conditions:
        return True

    if conditions.get("own_only") and ctx.get("owner_id") != ctx.get("user_id"):
        return False

    for key in ("warehouse_id", "branch_id", "org_id"):
        if key in conditions and ctx.get(key) != conditions[key]:
            return False

    if "min_amount" in conditions and float(ctx.get("amount", 0)) < float(
        conditions["min_amount"]
    ):
        return False

    if "max_amount" in conditions and float(ctx.get("amount", 0)) > float(
        conditions["max_amount"]
    ):
        return False

    return True


__all__ = [
    "is_allowed",
    "invalidate_policy_cache",
    "role_dominates",
]
