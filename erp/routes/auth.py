# erp/routes/auth.py
from flask import Blueprint, request, render_template, abort

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.get("/login")
def login_page():
    role = request.args.get("role", "client").lower()
    if role not in {"admin", "employee", "client"}:
        abort(404)
    return render_template("auth/login.html", role=role)

# Optional: accept POST later for real auth
@auth_bp.post("/login")
def login_post():
    # TODO: authenticate user; on success: login_user(user)
    role = request.form.get("role") or "client"
    return render_template("auth/login.html", role=role, message="(stub) Not implemented yet")
