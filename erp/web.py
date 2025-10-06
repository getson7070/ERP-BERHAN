from flask import Blueprint, render_template, redirect, url_for

web_bp = Blueprint("web", __name__)

# Existing routes...
# @web_bp.get("/choose_login") ...

# Legacy/aliases:
@web_bp.get("/login")
def login_root_alias():
    return redirect(url_for("auth.login"))

@web_bp.get("/employee_login")
def employee_login_alias():
    return redirect(url_for("auth.login", role="employee"))

@web_bp.get("/admin_login")
def admin_login_alias():
    return redirect(url_for("auth.login", role="admin"))

@web_bp.get("/company_login")
def company_login_alias():
    return redirect(url_for("auth.login", role="company"))
