# erp/routes/auth.py
from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length

bp = Blueprint("auth", __name__, url_prefix="/auth")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=64)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=2, max=128)])

@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # TODO: replace with your real authentication.
        session["user"] = form.username.data
        flash("Logged in successfully.", "success")
        # Send users somewhere useful if dashboard exists, otherwise home.
        try:
            return redirect(url_for("dashboard.index"))
        except Exception:
            return redirect(url_for("index"))
    return render_template("auth/login.html", form=form)

@bp.route("/logout", methods=["POST", "GET"])
def logout():
    session.pop("user", None)
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))
