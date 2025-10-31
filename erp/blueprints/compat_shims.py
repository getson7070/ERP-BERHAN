from __future__ import annotations
from flask import Blueprint, redirect, url_for, session

COMPAT_BLUEPRINT = Blueprint("compat_shims", __name__)

def _safe(url_endpoint: str, fallback: str | None = None):
    try:
        return url_for(url_endpoint)
    except Exception:
        if fallback:
            return url_for(fallback)
        raise

COMPAT_BLUEPRINT.add_url_rule(
    "/auth/choose", endpoint="auth.choose_login",
    view_func=lambda: redirect(_safe("auth.login")), methods=["GET"],
)

COMPAT_BLUEPRINT.add_url_rule(
    "/health", endpoint="health.health",
    view_func=lambda: redirect(_safe("health_bp.health", fallback="health_compat.health")),
    methods=["GET"],
)

COMPAT_BLUEPRINT.add_url_rule(
    "/hr/add", endpoint="hr.add_employee",
    view_func=lambda: redirect(_safe("hr.index")), methods=["GET"],
)

def _logout():
    session.clear()
    return redirect(_safe("login_ui.login", fallback="auth.login"))

COMPAT_BLUEPRINT.add_url_rule(
    "/logout", endpoint="login_ui.logout", view_func=_logout, methods=["GET","POST"],
)

COMPAT_BLUEPRINT.add_url_rule(
    "/tenders", endpoint="tenders.tenders_list",
    view_func=lambda: redirect(_safe("projects.index", fallback="orders.index")),
    methods=["GET"],
)

COMPAT_BLUEPRINT.add_url_rule(
    "/user_management/approve", endpoint="user_management.approve_client",
    view_func=lambda: redirect(_safe("crm.index", fallback="main.index")), methods=["GET","POST"],
)

COMPAT_BLUEPRINT.add_url_rule(
    "/user_management/create_employee", endpoint="user_management.create_employee",
    view_func=lambda: redirect(_safe("hr.index", fallback="main.index")), methods=["GET","POST"],
)

COMPAT_BLUEPRINT.add_url_rule(
    "/user_management/edit", endpoint="user_management.edit_user",
    view_func=lambda: redirect(_safe("hr.index", fallback="main.index")), methods=["GET","POST"],
)

COMPAT_BLUEPRINT.add_url_rule(
    "/user_management/delete", endpoint="user_management.delete_user",
    view_func=lambda: redirect(_safe("hr.index", fallback="main.index")), methods=["GET","POST"],
)

COMPAT_BLUEPRINT.add_url_rule(
    "/user_management/reject", endpoint="user_management.reject_client",
    view_func=lambda: redirect(_safe("crm.index", fallback="main.index")), methods=["GET","POST"],
)
