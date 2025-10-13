# erp/routes/auth.py
import os
from flask import Blueprint, abort, render_template

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def _enabled(role: str) -> bool:
    if role == "client":
        return os.getenv("ENABLE_CLIENT_LOGIN", "false").lower() == "true"
    if role == "employee":
        return os.getenv("ENABLE_EMPLOYEE_LOGIN", "false").lower() == "true"
    if role == "admin":
        return os.getenv("ENABLE_ADMIN_LOGIN", "false").lower() == "true"
    return False

@auth_bp.route("/login/<role>", methods=["GET"], endpoint="login")
def login(role: str):
    if role not in {"client", "employee", "admin"}:
        abort(404)
    if not _enabled(role):
        abort(404)
    # If you have specific templates per role, render them; otherwise show a simple stub.
    tmpl = f"auth/login_{role}.html"
    try:
        return render_template(tmpl)
    except Exception:
        # Minimal stub to avoid 500s while front-end is not wired yet
        return f"{role.capitalize()} login coming soon.", 200

# Convenience endpoints so url_for('auth.login_client') also works
@auth_bp.route("/login/client", endpoint="login_client")
def login_client():
    return login("client")

@auth_bp.route("/login/employee", endpoint="login_employee")
def login_employee():
    return login("employee")

@auth_bp.route("/login/admin", endpoint="login_admin")
def login_admin():
    return login("admin")
