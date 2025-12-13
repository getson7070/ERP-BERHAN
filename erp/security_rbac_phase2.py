"""Policy-based RBAC evaluator (Phase-2).

This engine evaluates allow/deny rules with support for:
- Wildcards (fnmatch) on resource and action
- Simple conditions (amount limits, ownership rules)
- Role alias normalization (manager/management/supervisor -> management_supervisor)
- Optional role hierarchy expansion (RoleHierarchy), if configured

Deny wins over allow.
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
from erp.rbac.defaults import DEFAULT_POLICY_NAME, ROLE_ALIASES, canonical_role, iter_default_rules


@lru_cache(maxsize=2048)
def _load_rules(org_id: int) -> list[RBACPolicyRule]:
    policies: Iterable[RBACPolicy] = (
        RBACPolicy.query.filter_by(org_id=org_id, is_active=True)
        .order_by(RBACPolicy.priority.asc())
        .all()
    )
    rules: list[RBACPolicyRule] = []
    for policy in policies:
        # policy.rules relationship should already be ordered/loaded
        rules.extend(policy.rules)
    return rules


def invalidate_policy_cache() -> None:
    """Clear in-memory cached policy rules."""
    _load_rules.cache_clear()


def ensure_default_policy(org_id: int) -> None:
    """Create a default policy with baseline rules when none exist.

    This is a safety net so an org is never "locked out" due to missing rules.
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
                effect=rule_dict["effect"],
                condition_json=rule_dict.get("condition_json") or {},
            )
        )

    db.session.add_all(rules)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Another worker likely seeded the policy concurrently; safe to ignore.


def _normalize_roles(user_roles: Iterable[str]) -> set[str]:
    """Normalize role keys for policy evaluation (lowercase + alias mapping)."""
    normalized: set[str] = set()
    for r in user_roles or []:
        rr = canonical_role(str(r))
        if rr:
            normalized.add(rr)
    return normalized


@lru_cache(maxsize=2048)
def _expand_roles_with_hierarchy(org_id: int, roles_frozenset: frozenset[str]) -> frozenset[str]:
    """Expand roles using RoleHierarchy table if present.

    If RoleHierarchy rows exist, we treat them as 'parent_role dominates child_role',
    and expand the user's effective roles to include dominated roles.
    """
    roles = set(roles_frozenset)
    # Fast path: if no hierarchy rows exist for org, skip expansion.
    if RoleHierarchy.query.filter_by(org_id=org_id).limit(1).count() == 0:
        return frozenset(roles)

    # Build adjacency: parent -> children
    rows = RoleHierarchy.query.filter_by(org_id=org_id).all()
    children_map: dict[str, set[str]] = {}
    for row in rows:
        parent = canonical_role(row.parent_role)
        child = canonical_role(row.child_role)
        children_map.setdefault(parent, set()).add(child)

    # BFS expansion
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
    """Evaluate allow/deny rules for a user (deny wins).

    Wildcards are supported on resource/action.
    Role aliases are normalized and (optionally) expanded via RoleHierarchy.
    """
    ctx = ctx or {}

    # Ensure org has baseline rules
    ensure_default_policy(org_id)

    roles = _normalize_roles(user_roles)
    roles = set(_expand_roles_with_hierarchy(org_id, frozenset(roles)))

    rules = _load_rules(org_id)
    matched_allow = False

    for rule in rules:
        # Normalize rule role key too (defensive)
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
    """Evaluate simple conditions.

    Supported:
    - own_only: ctx["owner_id"] must equal ctx["actor_id"]
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


__all__ = [
    "is_allowed",
    "invalidate_policy_cache",
    "ensure_default_policy",
]
