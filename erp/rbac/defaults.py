"""Baseline RBAC permission matrix for core ERP workflows.

This module centralises default permission rules and legacy permission key
translations so we can bootstrap a minimum viable policy set per organisation
without blocking existing role-based checks.

IMPORTANT GOVERNANCE RULE:
- The policy engine must use a canonical role vocabulary.
- We keep a limited alias map for backward compatibility while routes/models
  are migrated (e.g., "manager" -> "management_supervisor").
"""

from __future__ import annotations

from typing import Iterable

DEFAULT_POLICY_NAME = "Default Permission Matrix"

# ---------------------------------------------------------------------------
# Canonical role vocabulary (policy truth)
# ---------------------------------------------------------------------------
CANONICAL_ROLES = {
    "admin",
    "management_supervisor",
    "client",
    # Department / employee roles (extend as needed)
    "sales",
    "maintenance",
    "dispatch",
    "procurement",
    "inventory",
    "finance",
    "tender",
    "marketing",
    "hr",
    "analytics",
    "compliance",
    "audit",
}

# Backward compatible aliases for roles already used across routes / DB.
# This prevents authorization breakage while we migrate routes to require_permission.
ROLE_ALIASES = {
    "manager": "management_supervisor",
    "management": "management_supervisor",
    "supervisor": "management_supervisor",
}

def canonical_role(role_key: str) -> str:
    """Return canonical role for policy evaluation."""
    role_key = (role_key or "").strip().lower()
    return ROLE_ALIASES.get(role_key, role_key)

# ---------------------------------------------------------------------------
# Default permission rules
# ---------------------------------------------------------------------------
# Note: These are baseline rules. Administrators can override in the RBAC policy tables.
# Deny rules can be added later to restrict specific actions.
DEFAULT_PERMISSION_RULES = [
    # Admin: everything
    {"role": "admin", "resource": "*", "action": "*", "effect": "allow"},

    # Management supervisor: approvals and oversight across major workflows
    {"role": "management_supervisor", "resource": "orders", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "clients", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "maintenance_*", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "procurement", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "analytics", "action": "view", "effect": "allow"},

    # Sales: create/view/update orders (approval can be limited to supervisor if desired)
    {"role": "sales", "resource": "orders", "action": "view", "effect": "allow"},
    {"role": "sales", "resource": "orders", "action": "create", "effect": "allow"},
    {"role": "sales", "resource": "orders", "action": "update", "effect": "allow"},

    # Maintenance team: assets + work orders
    {"role": "maintenance", "resource": "maintenance_assets", "action": "*", "effect": "allow"},
    {"role": "maintenance", "resource": "maintenance_work_orders", "action": "*", "effect": "allow"},
    {"role": "maintenance", "resource": "maintenance_events", "action": "*", "effect": "allow"},
    {"role": "maintenance", "resource": "maintenance_kpi", "action": "view", "effect": "allow"},

    # Dispatch: workflow actions on work orders (start/check-in/complete)
    {"role": "dispatch", "resource": "maintenance_work_orders", "action": "view", "effect": "allow"},
    {"role": "dispatch", "resource": "maintenance_work_orders", "action": "start", "effect": "allow"},
    {"role": "dispatch", "resource": "maintenance_work_orders", "action": "checkin", "effect": "allow"},
    {"role": "dispatch", "resource": "maintenance_work_orders", "action": "complete", "effect": "allow"},
    {"role": "dispatch", "resource": "maintenance_events", "action": "view", "effect": "allow"},

    # Client: view and create maintenance work orders + view events (scope checks happen in route logic)
    {"role": "client", "resource": "maintenance_work_orders", "action": "view", "effect": "allow"},
    {"role": "client", "resource": "maintenance_work_orders", "action": "create", "effect": "allow"},
    {"role": "client", "resource": "maintenance_events", "action": "view", "effect": "allow"},

    # Procurement + inventory: procurement ticketing
    {"role": "procurement", "resource": "procurement", "action": "*", "effect": "allow"},
    {"role": "inventory", "resource": "procurement", "action": "view", "effect": "allow"},
    {"role": "inventory", "resource": "procurement", "action": "create", "effect": "allow"},
]


def iter_default_rules(org_id: int) -> Iterable[dict]:
    """Yield default rule dictionaries with the provided org id attached."""
    for rule in DEFAULT_PERMISSION_RULES:
        yield {
            "org_id": org_id,
            "role_key": canonical_role(rule["role"]),
            "resource": rule["resource"],
            "action": rule["action"],
            "effect": rule.get("effect", "allow"),
            "condition_json": rule.get("conditions", {}),
        }


__all__ = [
    "DEFAULT_POLICY_NAME",
    "DEFAULT_PERMISSION_RULES",
    "ROLE_ALIASES",
    "CANONICAL_ROLES",
    "canonical_role",
    "iter_default_rules",
]
