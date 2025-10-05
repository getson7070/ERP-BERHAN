# erp/routes/auth.py
from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length

bp = Blueprint("auth", __name__, url_prefix="/auth")
# Export alias so app.py can import `auth_bp` OR we can import `bp as auth_bp`.
auth_bp = bp
__all__ = ["bp", "auth_bp"]


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=64)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=2, max=128)])


@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # TODO: replace with real authentication
        session["user"] = form.username.data
        flash("Logged in successfully.", "success")
        # if you later add a dashboard blueprint, this will work automatically
        try:
            return redirect(url_for("dashboard.index"))
        except Exception:
            return redirect(url_for("web.index"))
    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("user", None)
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))
