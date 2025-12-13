"""Policy-based RBAC evaluator (Phase-2).

This evaluator enforces allow/deny rules with:
- Wildcards (fnmatch) on resource and action
- Simple conditions (amount limits, ownership rules)
- Canonical role normalisation and backward-compatible role aliases
- Optional role hierarchy expansion (RoleHierarchy), if configured

Governance rule: DENY overrides ALLOW.
"""

from __future__ import annotations

from collections import deque
from fnmatch import fnmatch
from functools import lru_cache
from typing import Iterable

from flask import current_app
from sqlalchemy.exc import IntegrityError

from erp.extensions import db
from erp.models import RBACPolicy, RBACPolicyRule, RoleHierarchy
from erp.rbac.defaults import DEFAULT_POLICY_NAME, canonical_role, iter_default_rules


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
    """Clear cached policy rules."""
    _load_rules.cache_clear()
    _expand_roles_with_hierarchy.cache_clear()


def ensure_default_policy(org_id: int) -> None:
    """Create a default policy with baseline rules when none exist.

    This prevents an org from being locked out due to missing policy rows.
    """
    if RBACPolicy.query.filter_by(org_id=org_id).count():
        return

    policy = RBACPolicy(org_id=org_id, name=DEFAULT_POLICY_NAME, is_active=True, priority=100)
    db.session.add(policy)
    db.session.flush()

    rules = []
    for rule_dict in iter_default_rules(org_id):
        rules.append(
            RBACPolicyRule(
                org_id=org_id,
                policy_id=policy.id,
                role_key=rule_dict["role_key"],
                resource=rule_dict["resource"],
                action=rule_dict["action"],
                effect=rule_dict.get("effect", "allow"),
                condition_json=rule_dict.get("condition_json") or {},
            )
        )

    db.session.add_all(rules)

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


def _normalize_roles(user_roles: Iterable[str]) -> set[str]:
    """Normalize role keys for policy evaluation."""
    normalized: set[str] = set()
    for r in user_roles or []:
        rr = canonical_role(str(r))
        if rr:
            normalized.add(rr)
    return normalized


@lru_cache(maxsize=2048)
def _expand_roles_with_hierarchy(org_id: int, roles_frozenset: frozenset[str]) -> frozenset[str]:
    """Expand roles using RoleHierarchy if configured.

    RoleHierarchy rows are interpreted as: parent_role dominates child_role.
    The user's effective roles are expanded to include any dominated roles.
    """
    roles = set(roles_frozenset)

    # Fast path if no hierarchy exists
    if RoleHierarchy.query.filter_by(org_id=org_id).limit(1).count() == 0:
        return frozenset(roles)

    rows = RoleHierarchy.query.filter_by(org_id=org_id).all()
    children_map: dict[str, set[str]] = {}
    for row in rows:
        parent = canonical_role(row.parent_role)
        child = canonical_role(row.child_role)
        children_map.setdefault(parent, set()).add(child)

    q = deque(list(roles))
    while q:
        parent = q.popleft()
        for child in children_map.get(parent, set()):
            if child not in roles:
                roles.add(child)
                q.append(child)

    return frozenset(roles)


def is_allowed(
    org_id: int,
    user_roles: Iterable[str],
    resource: str,
    action: str,
    ctx: dict | None = None,
) -> bool:
    """Evaluate allow/deny rules for a user (deny wins)."""
    ctx = ctx or {}
    ensure_default_policy(int(org_id))

    roles = _normalize_roles(user_roles)
    roles = set(_expand_roles_with_hierarchy(int(org_id), frozenset(roles)))

    rules = _load_rules(int(org_id))
    matched_allow = False

    for rule in rules:
        rule_role = canonical_role(rule.role_key)
        if rule_role not in roles:
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
    """Evaluate simple conditions for a rule.

    Supported:
    - own_only: ctx["owner_id"] == ctx["actor_id"]
    - min_amount/max_amount: compare ctx["amount"]
    """
    if not conditions:
        return True

    if conditions.get("own_only"):
        if str(ctx.get("owner_id")) != str(ctx.get("actor_id")):
            return False

    if "min_amount" in conditions and float(ctx.get("amount", 0)) < float(conditions["min_amount"]):
        return False

    if "max_amount" in conditions and float(ctx.get("amount", 0)) > float(conditions["max_amount"]):
        return False

    return True


__all__ = ["ensure_default_policy", "invalidate_policy_cache", "is_allowed"]
