# erp/routes/auth.py
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user
from ..models import User, DeviceAuthorization
from ..extensions import db

bp = Blueprint("auth", __name__, url_prefix="/auth")

def get_device_id_from_request():
    return request.args.get("device") or request.headers.get("X-Device-Id")

@bp.route("/login", methods=["GET", "POST"])
def login():
    role = request.args.get("role", "client")  # client / employee / admin
    if request.method == "GET":
        return render_template("auth/login.html", role=role)

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    device_id = get_device_id_from_request()

    user = User.query.filter_by(email=email, role=role, is_active=True).first()
    if not user or not user.check_password(password):
        flash("Invalid credentials", "error")
        return render_template("auth/login.html", role=role), 401

    if device_id and role in ("employee", "admin"):
        allowed = DeviceAuthorization.query.filter_by(
            user_id=user.id, device_id=device_id, allowed=True
        ).first()
        if not allowed:
            flash("This device is not authorized for your account.", "error")
            return render_template("auth/login.html", role=role), 403

    login_user(user)
    return redirect(url_for("main.index"))
