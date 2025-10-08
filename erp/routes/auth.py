# erp/routes/auth.py
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from .extensions import db
from .models import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.get("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    role = (request.args.get("role") or "client").lower()
    if role not in {"admin", "employee", "client"}:
        role = "client"
    return render_template("auth/login.html", role=role)

@auth_bp.post("/login")
def login_post():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    role = (request.form.get("role") or "client").lower()

    user = User.query.filter_by(email=email, role=role).first()
    if not user or not user.check_password(password):
        return render_template("auth/login.html", role=role, message="Invalid credentials"), 401

    login_user(user, remember=True)
    return redirect(url_for("main.dashboard"))

@auth_bp.get("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for("main.choose_login"))
