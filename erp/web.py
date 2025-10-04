# erp/web.py
from flask import Blueprint, render_template, redirect, url_for, current_app

web_bp = Blueprint("web", __name__)

@web_bp.route("/")
def home():
    """
    Default landing page:
    - If templates/login.html exists, show it.
    - If templates/index.html exists (SPA), show it.
    - Else show a helpful message.
    """
    for candidate in ("login.html", "index.html"):
        try:
            return render_template(candidate)
        except Exception:
            continue
    current_app.logger.warning(
        "No login.html or index.html found under erp/templates/. "
        "Showing fallback message."
    )
    return (
        "<h2>ERP-BERHAN is running.</h2>"
        "<p>Add <code>erp/templates/login.html</code> or "
        "<code>erp/templates/index.html</code> to render the UI here.</p>"
        "<p>Health: <a href='/health'>/health</a></p>",
        200,
    )

@web_bp.route("/login")
def login():
    try:
        return render_template("login.html")
    except Exception:
        # Fallback if template missing
        return (
            "<h3>Missing template: templates/login.html</h3>"
            "<p>Create it under <code>erp/templates/login.html</code>.</p>",
            200,
        )

@web_bp.route("/dashboard")
def dashboard():
    try:
        return render_template("dashboard.html")
    except Exception:
        return (
            "<h3>Missing template: templates/dashboard.html</h3>"
            "<p>Create it under <code>erp/templates/dashboard.html</code>.</p>",
            200,
        )
