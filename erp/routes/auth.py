# erp/routes/auth.py
from __future__ import annotations
from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login/<role>")
def login(role: str):
    """
    Single endpoint used by templates via: url_for('auth.login', role='client'|'employee'|'admin')
    Tries role-specific template, then a generic fallback, then plain text.
    """
    role = (role or "").lower()
    allowed = {"client", "employee", "admin"}
    if role not in allowed:
        abort(404)

    candidates = [f"auth/login_{role}.html", "auth/login.html"]
    for tpl in candidates:
        try:
            return render_template(tpl, role=role)
        except TemplateNotFound:
            continue
    return f"{role.capitalize()} login page", 200
