"""Baseline RBAC permission matrix for core ERP workflows."""

from __future__ import annotations

from typing import Iterable

DEFAULT_POLICY_NAME = "Default Permission Matrix"

CANONICAL_ROLES = {
    "admin",
    "management_supervisor",
    "client",
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
    "crm",
    "compliance",
    "audit",
}

ROLE_ALIASES = {
    "manager": "management_supervisor",
    "management": "management_supervisor",
    "supervisor": "management_supervisor",
}


def canonical_role(role_key: str) -> str:
    role_key = (role_key or "").strip().lower()
    return ROLE_ALIASES.get(role_key, role_key)


DEFAULT_PERMISSION_RULES: list[dict] = [
    {"role": "admin", "resource": "*", "action": "*", "effect": "allow"},

    {"role": "management_supervisor", "resource": "admin_console", "action": "view", "effect": "allow"},
    {"role": "management_supervisor", "resource": "clients", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "orders", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "maintenance_work_orders", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "maintenance_assets", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "maintenance_events", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "procurement", "action": "*", "effect": "allow"},
    {"role": "management_supervisor", "resource": "analytics", "action": "view", "effect": "allow"},
    {"role": "management_supervisor", "resource": "banking", "action": "view", "effect": "allow"},
    {"role": "management_supervisor", "resource": "audit", "action": "view", "effect": "allow"},
    {"role": "management_supervisor", "resource": "commissions", "action": "view", "effect": "allow"},

    {"role": "sales", "resource": "orders", "action": "view", "effect": "allow"},
    {"role": "sales", "resource": "orders", "action": "create", "effect": "allow"},
    {"role": "sales", "resource": "orders", "action": "update", "effect": "allow"},
    {"role": "sales", "resource": "crm", "action": "view", "effect": "allow"},
    {"role": "sales", "resource": "crm", "action": "manage", "effect": "allow"},

    {"role": "crm", "resource": "crm", "action": "*", "effect": "allow"},

    {"role": "maintenance", "resource": "maintenance_assets", "action": "*", "effect": "allow"},
    {"role": "maintenance", "resource": "maintenance_work_orders", "action": "*", "effect": "allow"},
    {"role": "maintenance", "resource": "maintenance_events", "action": "*", "effect": "allow"},
    {"role": "maintenance", "resource": "analytics", "action": "view", "effect": "allow"},

    {"role": "dispatch", "resource": "maintenance_work_orders", "action": "view", "effect": "allow"},
    {"role": "dispatch", "resource": "maintenance_work_orders", "action": "start", "effect": "allow"},
    {"role": "dispatch", "resource": "maintenance_work_orders", "action": "checkin", "effect": "allow"},
    {"role": "dispatch", "resource": "maintenance_work_orders", "action": "complete", "effect": "allow"},
    {"role": "dispatch", "resource": "maintenance_events", "action": "view", "effect": "allow"},

    {"role": "client", "resource": "maintenance_work_orders", "action": "view", "effect": "allow"},
    {"role": "client", "resource": "maintenance_work_orders", "action": "create", "effect": "allow"},
    {"role": "client", "resource": "maintenance_events", "action": "view", "effect": "allow"},
    {"role": "client", "resource": "orders", "action": "view", "effect": "allow"},
    {"role": "client", "resource": "orders", "action": "create", "effect": "allow"},
    {"role": "client", "resource": "client_portal", "action": "view", "effect": "allow"},

    {"role": "procurement", "resource": "procurement", "action": "*", "effect": "allow"},
    {"role": "inventory", "resource": "procurement", "action": "view", "effect": "allow"},
    {"role": "inventory", "resource": "procurement", "action": "create", "effect": "allow"},

    {"role": "analytics", "resource": "analytics", "action": "view", "effect": "allow"},
    {"role": "analytics", "resource": "analytics", "action": "manage", "effect": "allow"},

    {"role": "finance", "resource": "banking", "action": "*", "effect": "allow"},
    {"role": "finance", "resource": "commissions", "action": "view", "effect": "allow"},
    {"role": "finance", "resource": "commissions", "action": "pay", "effect": "allow"},

    {"role": "audit", "resource": "audit", "action": "view", "effect": "allow"},
    {"role": "audit", "resource": "audit", "action": "export", "effect": "allow"},
    {"role": "compliance", "resource": "audit", "action": "view", "effect": "allow"},
    {"role": "compliance", "resource": "audit", "action": "export", "effect": "allow"},
]

LEGACY_PERMISSION_KEY_MAP: dict[str, tuple[str, str]] = {
    "add_tender": ("tenders", "create"),
    "tenders_list": ("tenders", "view"),
    "tenders_report": ("tenders", "report"),
}


def iter_default_rules(org_id: int) -> Iterable[dict]:
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
