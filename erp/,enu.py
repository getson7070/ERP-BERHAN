"""Request-safe navigation menu builder.

Menu items are defined by endpoint name (no url_for at import/app-init time)
and filtered at request-time using current_user.has_permission().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass(frozen=True)
class MenuItem:
    label: str
    endpoint: str
    permissions: Sequence[str] = ()
    icon: Optional[str] = None
    children: Sequence["MenuItem"] = ()


# Keep this list small and stable; expand as modules harden.
NAV_ITEMS: Sequence[MenuItem] = (
    MenuItem("Dashboard", "main.index", ("view_dashboard",), icon="bi-speedometer2"),
    MenuItem("Orders", "orders.index", ("view_orders",), icon="bi-bag-check"),
    MenuItem("Inventory", "inventory.index", ("view_inventory",), icon="bi-box-seam"),
    MenuItem("Maintenance", "maintenance.index", ("view_maintenance",), icon="bi-tools"),
    MenuItem("Tenders", "tenders.list", ("view_tenders",), icon="bi-file-earmark-text"),
    MenuItem("Procurement", "procurement.index", ("manage_procurement",), icon="bi-truck"),
    MenuItem("CRM", "crm.index", ("view_crm",), icon="bi-people"),
    MenuItem("Analytics", "analytics.dashboard", ("view_dashboard", "view_analytics"), icon="bi-graph-up"),
    MenuItem("Admin", "admin.index", ("manage_users",), icon="bi-shield-lock"),
)


def _allowed(user, item: MenuItem) -> bool:
    if not item.permissions:
        return True
    # Admin/management wildcard should already be handled in User.has_permission()
    for p in item.permissions:
        if user.has_permission(p):
            return True
    return False


def build_nav_menu(user) -> List[dict]:
    """Return a JSON-serializable menu structure for templates."""
    out: List[dict] = []
    for item in NAV_ITEMS:
        if not _allowed(user, item):
            continue

        children = []
        for c in item.children:
            if _allowed(user, c):
                children.append({"label": c.label, "endpoint": c.endpoint, "icon": c.icon})

        out.append(
            {
                "label": item.label,
                "endpoint": item.endpoint,
                "icon": item.icon,
                "children": children,
            }
        )
    return out
