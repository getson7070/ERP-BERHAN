# erp/routes/auth.py — complete login
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user
from ..extensions import db, login_manager
from ..models import User, DeviceAuthorization

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/login", methods=["GET", "POST"])
def login():
    role = request.args.get("role", "client")
    if request.method == "GET":
        return render_template("auth/login.html", role=role)

    email = request.form.get("email") or (request.json and request.json.get("email"))
    password = request.form.get("password") or (request.json and request.json.get("password"))
    device_id = request.args.get("device") or request.headers.get("X-Device-Id")

    if not email or not password:
        flash("Email and password are required.", "error")
        return render_template("auth/login.html", role=role), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        flash("Invalid credentials", "error")
        return render_template("auth/login.html", role=role), 401

    # Device gating for elevated roles
    if device_id and role in ("employee", "admin"):
        allowed = DeviceAuthorization.query.filter_by(user_id=user.id, device_id=device_id, allowed=True).first()
        if not allowed:
            flash("This device is not authorized for your account.", "error")
            return render_template("auth/login.html", role=role), 403

    login_user(user)
    return redirect(url_for("main.index"))
