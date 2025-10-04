# erp/routes/auth.py
from __future__ import annotations

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session
)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length

# Blueprint
bp = Blueprint("auth", __name__, url_prefix="/auth")
# Alias expected by app.py
auth_bp = bp


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

        # Safe "next" redirect (only same-site paths)
        next_url = request.args.get("next") or request.form.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)

        # Prefer your web blueprint index; fall back to root
        try:
            return redirect(url_for("web.index"))
        except Exception:
            return redirect("/")
    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))
