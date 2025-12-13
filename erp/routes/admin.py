"""Admin UI routes (HTML).

This module is intentionally thin: it renders admin pages while all state
changes are handled via policy-gated API endpoints.
"""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user

from erp.security_decorators_phase2 import require_permission
from erp.utils import resolve_org_id

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/")
@require_permission("admin_console", "view")
def index():
    """Admin dashboard landing page."""
    return render_template("admin/index.html")


@bp.get("/users")
@require_permission("users", "view")
def users():
    """User management UI."""
    return render_template("admin/users.html")


@bp.get("/roles")
@require_permission("users", "manage_roles")
def roles():
    """Role and permission management UI."""
    return render_template("admin/roles.html")


@bp.get("/clients")
@require_permission("clients", "view")
def clients():
    """Client onboarding and approval UI."""
    return render_template("admin/clients.html")


@bp.get("/approvals")
@require_permission("approvals", "view")
def approvals():
    """Order / workflow approval UI."""
    return render_template("admin/approvals.html")


@bp.get("/settings")
@require_permission("admin_console", "manage_settings")
def settings():
    """System-level configuration (admin only)."""
    return render_template("admin/settings.html")


@bp.get("/audit")
@require_permission("audit", "view")
def audit():
    """Audit log viewer."""
    return render_template("admin/audit.html")


@bp.get("/analytics")
@require_permission("analytics", "view")
def analytics():
    """Analytics dashboards."""
    return render_template("admin/analytics.html")


@bp.get("/banking")
@require_permission("banking", "view")
def banking():
    """Banking & finance dashboards."""
    return render_template("admin/banking.html")


@bp.get("/maintenance")
@require_permission("maintenance_work_orders", "view")
def maintenance():
    """Maintenance overview dashboard."""
    return render_template("admin/maintenance.html")


@bp.get("/procurement")
@require_permission("procurement", "view")
def procurement():
    """Procurement & import tracking dashboard."""
    return render_template("admin/procurement.html")
