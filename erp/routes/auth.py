# erp/routes/auth.py
from __future__ import annotations

from flask import Blueprint, current_app, render_template, request, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired

from erp.extensions import limiter, oauth, db, jwt, csrf
from erp.utils import login_required, verify_password  # keep your helpers

bp = Blueprint("auth", __name__)

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])

@bp.get("/login")
@limiter.limit("30/minute")
def login():
    form = LoginForm()
    return render_template("auth/login.html", form=form)

@bp.post("/login")
@limiter.limit("10/minute")
@csrf.exempt  # remove if your template includes {{ csrf_token() }}
def login_post():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        # TODO: fetch user from SQLAlchemy models
        # user = User.query.filter_by(username=username).first()
        user = None  # replace with real lookup
        if user and verify_password(user.password_hash, password):
            session["user_id"] = getattr(user, "id", username)
            flash("Logged in", "success")
            return redirect(url_for("main.dashboard"))
    flash("Invalid credentials", "danger")
    return redirect(url_for("auth.login"))

@bp.get("/logout")
def logout():
    session.clear()
    flash("Logged out", "success")
    return redirect(url_for("auth.login"))

@bp.get("/choose-login")
def choose_login():
    # You already have templates/choose_login.html
    return render_template("choose_login.html")
