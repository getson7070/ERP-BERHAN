"""Baseline RBAC permission matrix for core ERP workflows.

This module centralises default permission rules and legacy permission key
translations so we can bootstrap a minimum viable policy set per organisation
without blocking existing role-based checks. Rules intentionally use wildcard
resources/actions for compatibility and can be overridden by administrators
through the policy tables.
"""

from __future__ import annotations

from typing import Iterable

DEFAULT_POLICY_NAME = "Default Permission Matrix"

# Core resource/action rules applied when no organisation-specific policy
# exists. Role keys are stored in lowercase to match the runtime normalisation
# used in `erp.security._get_user_role_names`.
DEFAULT_PERMISSION_RULES: list[dict] = [
    # Administrative control
    {"role": "admin", "resource": "*", "action": "*", "effect": "allow"},
    {"role": "management", "resource": "orders:*", "action": "approve", "effect": "allow"},
    {"role": "supervisor", "resource": "orders:*", "action": "approve", "effect": "allow"},
    {"role": "management", "resource": "maintenance:*", "action": "approve", "effect": "allow"},
    {"role": "supervisor", "resource": "maintenance:*", "action": "approve", "effect": "allow"},
    {"role": "management", "resource": "procurement:*", "action": "approve", "effect": "allow"},
    {"role": "supervisor", "resource": "procurement:*", "action": "approve", "effect": "allow"},

    # Order lifecycle
    {"role": "employee", "resource": "orders", "action": "create", "effect": "allow"},
    {"role": "sales_rep", "resource": "orders", "action": "create", "effect": "allow"},
    {"role": "sales_rep", "resource": "orders", "action": "view", "effect": "allow"},
    {"role": "management", "resource": "orders", "action": "view", "effect": "allow"},

    # Commission and finance visibility (read-only by default)
    {"role": "management", "resource": "commission", "action": "view", "effect": "allow"},
    {"role": "supervisor", "resource": "commission", "action": "view", "effect": "allow"},

    # Maintenance lifecycle
    {"role": "employee", "resource": "maintenance", "action": "create", "effect": "allow"},
    {"role": "employee", "resource": "maintenance", "action": "view", "effect": "allow"},
    {"role": "biomedical_engineer", "resource": "maintenance", "action": "update", "effect": "allow"},

    # Procurement/import tracking
    {"role": "procurement", "resource": "procurement", "action": "create", "effect": "allow"},
    {"role": "procurement", "resource": "procurement", "action": "view", "effect": "allow"},

    # Reporting and analytics
    {"role": "management", "resource": "reports", "action": "view", "effect": "allow"},
    {"role": "supervisor", "resource": "reports", "action": "view", "effect": "allow"},

    # Telegram bot / automation hooks (limited until MFA-aware tokens exist)
    {"role": "employee", "resource": "bot", "action": "read", "effect": "allow"},
]


# Legacy permission keys used across older views (e.g. tenders). These map to
# canonical resource/action pairs for the policy engine.
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
            "role_key": rule["role"],
            "resource": rule["resource"],
            "action": rule["action"],
            "effect": rule.get("effect", "allow"),
            "condition_json": rule.get("conditions", {}),
        }


__all__ = [
    "DEFAULT_PERMISSION_RULES",
    "DEFAULT_POLICY_NAME",
    "LEGACY_PERMISSION_KEY_MAP",
    "iter_default_rules",
]
