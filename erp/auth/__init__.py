# erp/auth/__init__.py
from __future__ import annotations

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from werkzeug.urls import url_parse

from erp.forms import LoginForm
from erp.models.user import User  # adjust import path if your User lives elsewhere

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login view using Flask-WTF form + CSRF."""
    if current_user.is_authenticated:
        # Already logged in – send to dashboard or home
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        # never pre-fill admin email; just use what user gives
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)

        login_user(user)

        # Respect ?next= URL but don’t allow open redirect
        next_url = request.args.get("next")
        if not next_url or url_parse(next_url).netloc != "":
            next_url = url_for("main.dashboard")
        return redirect(next_url)

    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["POST"])
def logout():
    """Logout via POST to benefit from CSRF protection."""
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
