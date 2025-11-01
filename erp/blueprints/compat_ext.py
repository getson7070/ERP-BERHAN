from __future__ import annotations
from flask import Blueprint, redirect, url_for, session

# Process-level idempotency
_ADDED: set[tuple[str, str]] = set()

def _safe(ep: str, fallback: str | None = None) -> str:
    try:
        return url_for(ep)
    except Exception:
        if fallback:
            return url_for(fallback)
        raise

def _add_once(bp: Blueprint, rule: str, endpoint: str, view_func, methods=None):
    key = (bp.name, endpoint)
    if key in _ADDED:
        return
    # Blueprint-level light guard to avoid duplicates in deferred functions
    for fn in getattr(bp, "deferred_functions", []):
        try:
            code = getattr(fn, "__code__", None)
            consts = list(getattr(code, "co_consts", ())) if code else []
            if endpoint in map(str, consts):
                return
        except Exception:
            pass
    _ADDED.add(key)
    bp.add_url_rule(rule, endpoint=endpoint, view_func=view_func, methods=methods or ["GET"])

def _extend_existing_blueprints():
    added = []
    # /auth/choose -> auth.login
    try:
        from erp.routes.auth import bp as auth_bp
        _add_once(auth_bp, "/choose", "choose_login", lambda: redirect(_safe("auth.login")))
        added.append((auth_bp, "/auth"))
    except Exception:
        pass

    # /login_ui/logout -> clear and go to login
    try:
        from erp.blueprints.login_ui import bp as login_ui_bp
        def _logout():
            session.clear()
            return redirect(_safe("login_ui.login", fallback="auth.login"))
        _add_once(login_ui_bp, "/logout", "logout", _logout, methods=["GET","POST"])
        added.append((login_ui_bp, "/login_ui"))
    except Exception:
        pass

    # /hr/add -> hr.index
    try:
        from erp.routes.hr import bp as hr_bp
        _add_once(hr_bp, "/add", "add_employee", lambda: redirect(_safe("hr.index")))
        added.append((hr_bp, "/hr"))
    except Exception:
        pass

    return added

def _new_compat_blueprints():
    out = []

    # legacy health namespace -> canonical health
    health = Blueprint("health", __name__)
    _add_once(health, "/", "health",
        lambda: redirect(_safe("health_bp.health", fallback="health_compat.health")))
    out.append((health, "/health"))

    # legacy tenders list
    tenders = Blueprint("tenders", __name__)
    _add_once(tenders, "/", "tenders_list",
        lambda: redirect(_safe("projects.index", fallback="orders.index")))
    out.append((tenders, "/tenders"))

    # user_management legacy actions
    um = Blueprint("user_management", __name__)
    _add_once(um, "/approve", "approve_client",
        lambda: redirect(_safe("crm.index", fallback="main.index")), methods=["GET","POST"])
    _add_once(um, "/create", "create_employee",
        lambda: redirect(_safe("hr.index", fallback="main.index")), methods=["GET","POST"])
    _add_once(um, "/edit", "edit_user",
        lambda: redirect(_safe("hr.index", fallback="main.index")), methods=["GET","POST"])
    _add_once(um, "/delete", "delete_user",
        lambda: redirect(_safe("hr.index", fallback="main.index")), methods=["GET","POST"])
    _add_once(um, "/reject", "reject_client",
        lambda: redirect(_safe("crm.index", fallback="main.index")), methods=["GET","POST"])
    out.append((um, "/user_management"))

    return out

def extend_blueprints():
    """Single public API consumed by erp.__init__"""
    return _extend_existing_blueprints() + _new_compat_blueprints()
