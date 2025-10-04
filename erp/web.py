# erp/web.py
import os
from flask import Blueprint, render_template, redirect, url_for, jsonify
from jinja2 import TemplateNotFound
from flask_wtf import FlaskForm

# A harmless empty form so templates calling form.hidden_tag() won't crash
class EmptyForm(FlaskForm):
    pass

web_bp = Blueprint("web", __name__)

def _try_render(name: str):
    """
    Try to render a template by name from either templates/ or erp/templates/.
    Returns rendered HTML or None if not found.
    """
    try:
        # Pass an EmptyForm by default; safe if template doesn't use it
        return render_template(name, form=EmptyForm())
    except TemplateNotFound:
        return None

@web_bp.route("/health")
def health():
    # Expects 200 OK for uptime checks
    return jsonify(status="ok"), 200

@web_bp.route("/")
def index():
    # Prefer ENTRY_TEMPLATE if set; then common names
    candidates = []
    entry = os.getenv("ENTRY_TEMPLATE")
    if entry:
        candidates.append(entry.strip())

    candidates += [
        "choose_login.html",
        "auth/login.html",
        "login.html",
        "index.html",
    ]

    for name in candidates:
        html = _try_render(name)
        if html:
            return html

    # Final fallback so you at least see a page
    return (
        "ERP-BERHAN is running, but no entry template was found under "
        "`templates/` or `erp/templates/`.",
        200,
    )

@web_bp.route("/choose_login")
def choose_login():
    html = _try_render("choose_login.html")
    return html if html else redirect(url_for("web.index"))

@web_bp.route("/auth/login")
def auth_login():
    # If auth/login.html exists, show it; otherwise fall back
    html = _try_render("auth/login.html")
    return html if html else redirect(url_for("web.index"))
