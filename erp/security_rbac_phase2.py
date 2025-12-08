"""Policy-based RBAC evaluator (Phase-2).

The engine keeps compatibility with the existing role checks while enabling
admins to manage allow/deny rules, wildcards, and simple conditions.
"""

from __future__ import annotations

from fnmatch import fnmatch
from functools import lru_cache
from typing import Iterable

from flask import current_app
from sqlalchemy.exc import IntegrityError

from erp.extensions import db
from erp.models import RBACPolicy, RBACPolicyRule, RoleHierarchy
from erp.rbac.defaults import DEFAULT_POLICY_NAME, iter_default_rules


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


def ensure_default_policy(org_id: int) -> None:
    """Create a default policy with baseline rules when none exist.

    This function is idempotent and safe to call per-request; it short-circuits
    once a policy for the organisation is present. All rules are created within
    a single transaction to preserve compatibility if concurrent requests race
    to bootstrap permissions after deployment.
    """

    if not org_id:
        return

    existing = (
        RBACPolicy.query.filter_by(org_id=org_id)
        .with_entities(RBACPolicy.id)
        .first()
    )
    if existing:
        return

    policy = RBACPolicy(
        org_id=org_id,
        name=DEFAULT_POLICY_NAME,
        description="Auto-created baseline policy for core ERP workflows",
        priority=50,
    )

    for rule in iter_default_rules(org_id):
        policy.rules.append(RBACPolicyRule(**rule))

    db.session.add(policy)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        current_app.logger.info(
            "RBAC bootstrap skipped because another transaction created defaults",
            extra={"org_id": org_id},
        )
    else:
        invalidate_policy_cache()


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
    "ensure_default_policy",
]
