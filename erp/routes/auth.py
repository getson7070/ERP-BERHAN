# erp/routes/auth.py
from __future__ import annotations
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired
from erp.extensions import limiter, csrf

bp = Blueprint("auth", __name__)

class ChooseLoginForm(FlaskForm):
    login_type = SelectField("Login as", choices=[("employee","Employee"),("client","Client")])

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])

@bp.get("/choose-login")
def choose_login():
    form = ChooseLoginForm()
    return render_template("choose_login.html", form=form)

@bp.post("/choose-login")
def choose_login_post():
    form = ChooseLoginForm()
    if form.validate_on_submit():
        return redirect(url_for("auth.login"))
    return render_template("choose_login.html", form=form)

@bp.get("/login")
@limiter.limit("30/minute")
def login():
    form = LoginForm()
    return render_template("auth/login.html", form=form)

@bp.post("/login")
@csrf.exempt
@limiter.limit("10/minute")
def login_post():
    form = LoginForm()
    if form.validate_on_submit():
        # TODO: replace with real user lookup
        flash("Invalid credentials", "danger")
        return redirect(url_for("auth.login"))
    return render_template("auth/login.html", form=form)
