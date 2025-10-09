# erp/routes/auth.py
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, AnonymousUserMixin

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.get("/login")
def login():
    role = request.args.get("role", "employee")
    # Render a minimal page that does not require a form object
    return render_template("auth/login.html", role=role, form=None)

@auth_bp.post("/login")
def login_post():
    # Minimal, non-DB placeholder that always “logs in” an anonymous shell
    # Replace with real validation later to avoid silent registration failures.
    class _TempUser(AnonymousUserMixin):
        is_authenticated = True
        id = "temp-user"
        email = "temp@example.com"
        roles = ["admin"] if request.form.get("role") == "admin" else ["employee"]
        is_admin = "admin" in roles
        name = "Temporary User"

    login_user(_TempUser())  # type: ignore[arg-type]
    flash("Signed in (temporary stub). Replace with real auth.", "success")
    return redirect(url_for("main.choose_login"))

@auth_bp.post("/logout")
@login_required
def logout():
    from flask_login import logout_user
    logout_user()
    flash("Signed out.", "success")
    return redirect(url_for("main.choose_login"))
