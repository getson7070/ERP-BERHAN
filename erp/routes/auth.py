# erp/routes/auth.py
from __future__ import annotations

from flask import Blueprint, render_template, abort

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# Canonical endpoint: auth.login (requires a role)
@auth_bp.route("/login/<role>")
def login(role: str):
    role = (role or "").lower()
    if role not in {"client", "employee", "admin"}:
        abort(404)

    # Try role-specific template, fall back to generic
    for tpl in (f"auth/login_{role}.html", "auth/login.html"):
        try:
            return render_template(tpl, role=role)
        except Exception:
            # swallow TemplateNotFound and continue
            continue
    return f"{role.capitalize()} login", 200


# -------- Backward-compatibility aliases (so url_for('auth.login_client') etc. work) --------
@auth_bp.route("/login/client")
def login_client():
    return login("client")


@auth_bp.route("/login/employee")
def login_employee():
    return login("employee")


@auth_bp.route("/login/admin")
def login_admin():
    return login("admin")
