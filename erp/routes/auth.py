from __future__ import annotations

from typing import Optional
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, HiddenField
from wtforms.validators import DataRequired, Length, Optional as VOptional
from ..extensions import db
from ..models import User

try:
    import pyotp  # optional
except Exception:
    pyotp = None

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

class LoginForm(FlaskForm):
    username = StringField("Username or Email", validators=[DataRequired(), Length(min=2, max=128)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=2, max=128)])
    mac = StringField("MAC address", validators=[VOptional(), Length(min=2, max=64)])
    otp = StringField("One-time password", validators=[VOptional(), Length(min=6, max=10)])
    role = HiddenField("role")  # set by JS / query string

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    role = (request.args.get("role") or form.role.data or "client").strip().lower()
    form.role.data = role

    if request.method == "GET":
        return render_template("auth/login.html", form=form)

    if not form.validate_on_submit():
        flash("Please complete the form.", "error")
        return render_template("auth/login.html", form=form), 400

    ident = form.username.data.strip()
    user: Optional[User] = None
    if "@" in ident:
        user = User.query.filter(db.func.lower(User.email) == ident.lower()).first()
    if not user:
        user = User.query.filter(db.func.lower(User.username) == ident.lower()).first()

    if not user or user.role != role or not user.is_active:
        flash("Invalid credentials.", "error")
        return render_template("auth/login.html", form=form), 401

    if not user.check_password(form.password.data):
        flash("Invalid credentials.", "error")
        return render_template("auth/login.html", form=form), 401

    if role == "employee":
        expected = (user.mac_address or "").lower().strip()
        provided = (form.mac.data or "").lower().strip()
        if expected and provided != expected:
            flash("This device is not authorized for the employee account.", "error")
            return render_template("auth/login.html", form=form), 403

    if role == "admin" and user.otp_secret and pyotp is not None:
        if not form.otp.data:
            flash("Enter the OTP code.", "error")
            return render_template("auth/login.html", form=form), 400
        totp = pyotp.TOTP(user.otp_secret)
        if not totp.verify(form.otp.data, valid_window=1):
            flash("Invalid OTP code.", "error")
            return render_template("auth/login.html", form=form), 401

    login_user(user)

    # Try dashboard if it exists; otherwise back to chooser.
    for endpoint in ("dashboard.index",):
        try:
            return redirect(url_for(endpoint))
        except Exception:
            pass
    return redirect(url_for("web.choose_login"))

@auth_bp.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    flash("Logged out.", "ok")
    return redirect(url_for("auth.login"))
