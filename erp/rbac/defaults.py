"""Baseline RBAC permission matrix for core ERP workflows.

This module centralises default permission rules and legacy permission key
translations so we can bootstrap a minimum viable policy set per organisation
without blocking existing role-based checks.

Key design goals for ERP-BERHAN:
- Canonical role vocabulary for policy evaluation (admin / management_supervisor / departments / client)
- Backward-compatible role aliases while legacy role names still exist in the DB and routes
- Resource/action pairs (not combined strings) to avoid drift and ambiguity
"""

from __future__ import annotations

from typing import Iterable

DEFAULT_POLICY_NAME = "Default Permission Matrix"

# ---------------------------------------------------------------------------
# Canonical roles (policy truth)
# ---------------------------------------------------------------------------
CANONICAL_ROLES = {
    "admin",
    "management_supervisor",
    "client",
    # Departments / employee roles (extend as needed)
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

# Backward-compatible aliases used across older code and existing DB role rows.
# These aliases are resolved during policy evaluation.
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
# Default policy rules
# ---------------------------------------------------------------------------
# NOTE:
# - Resource/action values here must match how `require_permission(resource, action)`
#   is called from routes.
# - Admin is granted everything.
# - Management supervisor is granted approval and oversight across major workflows.
DEFAULT_PERMISSION_RULES: list[dict] = [
    # Administrative control
    {"role": "admin", "resource": "*", "action": "*", "effect": "allow"},

    # Management supervisor (approvals + oversight, not system RBAC editing)
    {"role": "management_supervisor", "resource": "admin_console", "action": "view", "effect": "allow"},
    {"role": "management_supervisor", "resource": "clients", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "orders", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "maintenance_work_orders", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "maintenance_assets", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "maintenance_events", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "procurement", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "analytics", "action": "view", "effect": "allow"},

    # Orders
    {"role": "sales", "resource": "orders", "action": "view", "effect": "allow"},
    {"role": "sales", "resource": "orders", "action": "create", "effect": "allow"},
    {"role": "sales", "resource": "orders", "action": "update", "effect": "allow"},

    # Maintenance team
    {"role": "maintenance", "resource": "maintenance_assets", "action": "*", "effect": "allow"},
    {"role": "maintenance", "resource": "maintenance_work_orders", "action": "*", "effect": "allow"},
    {"role": "maintenance", "resource": "maintenance_events", "action": "*", "effect": "allow"},
    {"role": "maintenance", "resource": "analytics", "action": "view", "effect": "allow"},

    # Dispatch (limited maintenance workflow)
    {"role": "dispatch", "resource": "maintenance_work_orders", "action": "view", "effect": "allow"},
    {"role": "dispatch", "resource": "maintenance_work_orders", "action": "start", "effect": "allow"},
    {"role": "dispatch", "resource": "maintenance_work_orders", "action": "checkin", "effect": "allow"},
    {"role": "dispatch", "resource": "maintenance_work_orders", "action": "complete", "effect": "allow"},
    {"role": "dispatch", "resource": "maintenance_events", "action": "view", "effect": "allow"},

    # Client (scoping is enforced in route logic; this is only capability)
    {"role": "client", "resource": "maintenance_work_orders", "action": "view", "effect": "allow"},
    {"role": "client", "resource": "maintenance_work_orders", "action": "create", "effect": "allow"},
    {"role": "client", "resource": "maintenance_events", "action": "view", "effect": "allow"},

    # Procurement
    {"role": "procurement", "resource": "procurement", "action": "*", "effect": "allow"},
    {"role": "inventory", "resource": "procurement", "action": "view", "effect": "allow"},
    {"role": "inventory", "resource": "procurement", "action": "create", "effect": "allow"},
]

# ---------------------------------------------------------------------------
# Legacy permission keys used across older views (e.g. tenders).
# These map to canonical resource/action pairs for the policy engine.
# ---------------------------------------------------------------------------
LEGACY_PERMISSION_KEY_MAP: dict[str, tuple[str, str]] = {
    "add_tender": ("tenders", "create"),
    "tenders_list": ("tenders", "view"),
    "tenders_report": ("tenders", "report"),
}


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
    "DEFAULT_PERMISSION_RULES",
    "DEFAULT_POLICY_NAME",
    "LEGACY_PERMISSION_KEY_MAP",
    "CANONICAL_ROLES",
    "ROLE_ALIASES",
    "canonical_role",
    "iter_default_rules",
]
