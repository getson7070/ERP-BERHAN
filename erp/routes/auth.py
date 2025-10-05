# erp/routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length
from flask_login import login_user, logout_user
import pyotp

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

class LoginForm(FlaskForm):
    username = StringField("Email or Username", validators=[DataRequired(), Length(min=2, max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    mac = StringField("Device MAC")  # shown/validated for employees
    otp = StringField("OTP")         # optional for admins if enabled

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    role = request.args.get("role", "client")  # admin | employee | client
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.username.data)
        ).first()

        if not user or not user.check_password(form.password.data):
            flash("Invalid credentials.", "danger")
            return render_template("auth/login.html", form=form, role=role)

        # Role gates
        if role == "employee":
            if not user.is_employee:
                flash("Not an employee account.", "danger")
                return render_template("auth/login.html", form=form, role=role)
            required_mac = (user.mac_address or "").strip().lower()
            provided_mac = (form.mac.data or "").strip().lower()
            if required_mac and provided_mac != required_mac:
                flash("This device (MAC) is not authorized.", "danger")
                return render_template("auth/login.html", form=form, role=role)

        if role == "admin":
            if not user.is_admin:
                flash("Not an admin account.", "danger")
                return render_template("auth/login.html", form=form, role=role)
            if user.otp_secret:
                token = (form.otp.data or "").strip()
                if not token or not pyotp.TOTP(user.otp_secret).verify(token, valid_window=1):
                    flash("Invalid or missing OTP.", "danger")
                    return render_template("auth/login.html", form=form, role=role)

        login_user(user)
        flash("Welcome back!", "success")
        # Try role dashboards if present, otherwise home
        for endpoint in (f"{role}.dashboard", "web.index"):
            try:
                return redirect(url_for(endpoint))
            except Exception:
                continue
        return redirect(url_for("web.index"))

    return render_template("auth/login.html", form=form, role=role)

@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))
