# erp/routes/auth.py
from flask import Blueprint, request, render_template, abort
from flask_login import current_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.get("/login")
def login():
    role = (request.args.get("role") or "client").lower()

    # Only "client" login is public. Admin/Employee requires prior auth with same role.
    if role in {"admin", "employee"}:
        if not current_user.is_authenticated or getattr(current_user, "role", None) != role:
            abort(403)

    return render_template("auth/login.html", role=role)

# Optional: add a simple 403 page
@auth_bp.app_errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403
