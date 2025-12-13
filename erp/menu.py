from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from flask import url_for
from werkzeug.routing import BuildError


@dataclass
class MenuItem:
    label: str
    endpoint: str
    icon: str = "bi-circle"
    permission: Optional[str] = None
    children: list["MenuItem"] = field(default_factory=list)
    external: bool = False


def _user_permission_set(user) -> set[str]:
    """
    Build a real permission set from DB relationships:
      user.roles -> role.permissions -> perm.code
    Falls back to empty set safely.
    """
    perms: set[str] = set()
    if not user or not getattr(user, "is_authenticated", False):
        return perms

    roles = getattr(user, "roles", []) or []
    for r in roles:
        for p in getattr(r, "permissions", []) or []:
            code = getattr(p, "code", None)
            if code:
                perms.add(str(code))
    return perms


def _is_admin(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    roles = [str(x).lower() for x in (getattr(user, "roles", []) or [])]
    # roles may be objects; also try role.name
    names = []
    for r in getattr(user, "roles", []) or []:
        rn = getattr(r, "name", None)
        if rn:
            names.append(str(rn).lower())
    roles = roles + names
    return any(x in ("admin", "superadmin", "management") for x in roles)


def _visible(item: MenuItem, permset: set[str], is_admin: bool) -> bool:
    if is_admin:
        return True
    if item.permission and item.permission not in permset:
        return False
    if item.children:
        return any(_visible(c, permset, is_admin) for c in item.children)
    return True


def _safe_url(endpoint: str) -> Optional[str]:
    try:
        return url_for(endpoint)
    except BuildError:
        return None


def build_menu_for_user(user) -> list[dict]:
    """
    Returns a structure ready for templates:
    [
      {"section": "Core", "items": [{"label":..., "url":..., "icon":..., "children":[...]}]}
    ]
    """
    permset = _user_permission_set(user)
    admin = _is_admin(user)

    # Define your navigation “truth” once here.
    # Visibility is automatically derived from real permissions in DB.
    tree: list[tuple[str, list[MenuItem]]] = [
        ("Core", [
            MenuItem("Home", "main.home", "bi-house"),
            MenuItem("Dashboard", "main.dashboard", "bi-speedometer2", permission="dashboard.view"),
        ]),
        ("Clients", [
            MenuItem("My Orders", "orders.client_orders", "bi-bag", permission="orders.client.view"),
            MenuItem("Maintenance", "maintenance.client_requests", "bi-tools", permission="maintenance.client.view"),
        ]),
        ("Operations", [
            MenuItem("Orders", "orders.list_orders", "bi-receipt", permission="orders.view"),
            MenuItem("Inventory", "inventory.list_items", "bi-box-seam", permission="inventory.view"),
            MenuItem("Maintenance Tickets", "maintenance.list_tickets", "bi-wrench", permission="maintenance.view"),
            MenuItem("Reports", "reports.index", "bi-graph-up", permission="reports.view"),
        ]),
        ("Administration", [
            MenuItem("Organizations", "orgs.index", "bi-buildings", permission="orgs.view"),
            MenuItem("Users", "users.index", "bi-people", permission="users.view"),
            MenuItem("Roles & Permissions", "rbac.index", "bi-shield-lock", permission="rbac.manage"),
            MenuItem("Audit Log", "audit.index", "bi-journal-text", permission="audit.view"),
        ]),
    ]

    rendered_sections: list[dict] = []

    for section, items in tree:
        section_items = []
        for it in items:
            if not _visible(it, permset, admin):
                continue

            url = _safe_url(it.endpoint)
            if not url:
                # If the endpoint isn’t registered yet, hide it instead of crashing the app.
                continue

            child_nodes = []
            for c in it.children:
                if not _visible(c, permset, admin):
                    continue
                cu = _safe_url(c.endpoint)
                if not cu:
                    continue
                child_nodes.append({
                    "label": c.label,
                    "url": cu,
                    "icon": c.icon,
                })

            section_items.append({
                "label": it.label,
                "url": url,
                "icon": it.icon,
                "children": child_nodes,
            })

        if section_items:
            rendered_sections.append({"section": section, "items": section_items})

    return rendered_sections
