# erp/routes/auth.py
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash

from erp.extensions import db  # <-- absolute import; fixes 'erp.routes.extensions' error

auth_bp = Blueprint("auth", __name__, template_folder="../../templates")


@auth_bp.get("/login")
def login():
    role = request.args.get("role", "employee")
    # Render form; the form posts back to /auth/login (below)
    return render_template("login.html", role=role)


@auth_bp.post("/login")
def do_login():
    role = request.form.get("role", "employee")
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    # Lazy import to avoid circulars if models import blueprints
    try:
        from erp.models import User  # type: ignore
    except Exception:
        flash("User model not available; contact admin.", "error")
        return render_template("login.html", role=role), 500

    user = db.session.execute(db.select(User).filter(User.email == email)).scalar_one_or_none()
    if not user:
        flash("Invalid credentials.", "error")
        return render_template("login.html", role=role), 401

    try:
        valid = (
            user.check_password(password) if hasattr(user, "check_password")
            else check_password_hash(getattr(user, "password_hash", ""), password)
        )
    except Exception:
        valid = False

    if not valid:
        flash("Invalid credentials.", "error")
        return render_template("login.html", role=role), 401

    login_user(user)
    flash("Welcome back!", "success")
    # Redirect per-role if you have dashboards, else home.
    return redirect(url_for("main.choose_login"))


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out.", "success")
    return redirect(url_for("main.choose_login"))
