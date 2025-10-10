# erp/routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from ..extensions import db
from ..models import User

bp = Blueprint("auth", __name__)

@bp.get("/login")
def login():
    role = request.args.get("role", "client")
    if role not in ("client",):  # only client login is public
        # redirect back to chooser if someone forces a guarded role
        return redirect(url_for("main.choose_login"))
    return render_template("auth/login.html", role=role)

@bp.post("/login")
def login_post():
    role = request.form.get("role", "client")
    email = request.form.get("email","").strip().lower()
    password = request.form.get("password","")
    user = User.query.filter_by(email=email, role=role).first()
    if not user or not user.check_password(password):
        flash("Invalid credentials", "error")
        return redirect(url_for("auth.login", role=role))
    login_user(user)
    return redirect(url_for("main.root"))

@bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.choose_login"))
