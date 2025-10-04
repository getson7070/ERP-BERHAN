from __future__ import annotations

import os
from typing import Iterable

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for
from jinja2 import TemplateNotFound
from wtforms import StringField, PasswordField, SubmitField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email

web_bp = Blueprint("web", __name__)

# Minimal WTForms login form so templates that call form.hidden_tag() / form.* render
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")

def _select_template(candidates: Iterable[str]) -> str | None:
    """Return the first existing template from the list, searching both loaders."""
    names = [n for n in candidates if n]
    try:
        # select_template raises if none exist
        t = current_app.jinja_env.select_template(names)
        return t.name
    except TemplateNotFound:
        return None

@web_bp.route("/health")
def health():
    return jsonify({"app": "ERP-BERHAN", "status": "running"})

@web_bp.route("/")
def root():
    # Let ENTRY_TEMPLATE override, else choose a sensible default
    entry = os.getenv("ENTRY_TEMPLATE")
    chosen = _select_template([
        entry,
        "auth/login.html",
        "choose_login.html",
        "login.html",
        "index.html",
    ])
    if not chosen:
        return (
            "ERP-BERHAN is running.<br><br>"
            "Expected one of: templates/auth/login.html, templates/choose_login.html, "
            "templates/login.html, templates/index.html.",
            200,
        )
    return render_template(chosen, form=LoginForm())

@web_bp.route("/login")
def login_page():
    chosen = _select_template([
        "auth/login.html",
        "login.html",
        "choose_login.html",
    ])
    if not chosen:
        return redirect(url_for("web.root"))
    return render_template(chosen, form=LoginForm())
