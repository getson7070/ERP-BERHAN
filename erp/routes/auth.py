# erp/routes/auth.py
from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional
from flask_login import login_user, logout_user, current_user
from sqlalchemy import or_

from ..extensions import db
from ..models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")
auth_bp = bp  # export alias

class LoginForm(FlaskForm):
    role = HiddenField("role", validators=[DataRequired()])  # 'admin' | 'employee' | 'client'
    username = StringField("Username or Email", validators=[DataRequired(), Length(min=2, max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=2, max=128)])
    mac_address = StringField("MAC Address", validators=[Optional(), Length(min=12, max=32)])
    otp = StringField("OTP", validators=[Optional(), Length(min=6, max=10)])

def _find_user_by_login(login: str, role: str) -> User | None:
    q = User.query.filter(User.role == role).filter(
        or_(User.username == login, User.email == login)
    )
    return q.first()

@bp.route("/login", methods=["GET", "POST"])
def login():
    # /auth/login?role=admin|employee|client (defaults to 'client')
    role = (request.args.get("role") or request.form.get("role") or "client").strip().lower()
    if role not in {"admin", "employee", "client"}:
        role = "client"

    form = LoginForm(role=role)

    if form.validate_on_submit():
        login_key = form.username.data.strip()
        user = _find_user_by_login(login_key, role)
        if not user or not user.is_active or not user.check_password(form.password.data):
            flash("Invalid credentials.", "danger")
            return render_template("auth/login.html", form=form, role=role), 401

        # Employee: require MAC match
        if role == "employee":
            mac = (form.mac_address.data or "").replace(":", "").replace("-", "").lower()
            if not mac or not user.mac_address or mac != user.mac_address.lower():
                flash("This device is not authorized (MAC mismatch).", "danger")
                return render_template("auth/login.html", form=form, role=role), 403

        # Admin: optional OTP
        if role == "admin" and user.otp_secret:
            # lazy import to keep deps optional if you don't set otp_secret
            import pyotp
            otp_ok = False
            code = (form.otp.data or "").strip()
            try:
                otp_ok = pyotp.TOTP(user.otp_secret).verify(code)
            except Exception:
                otp_ok = False
            if not otp_ok:
                flash("Invalid OTP.", "danger")
                return render_template("auth/login.html", form=form, role=role), 401

        login_user(user, remember=False)
        flash("Logged in successfully.", "success")

        # send users by role
        dest = {
            "admin": "admin.index",
            "employee": "employee.index",
            "client": "client.index",
        }.get(role, "web.index")
        try:
            return redirect(url_for(dest))
        except Exception:
            return redirect(url_for("web.index"))

    # GET or invalid POST
    return render_template("auth/login.html", form=form, role=role)

@bp.route("/logout", methods=["GET", "POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))
