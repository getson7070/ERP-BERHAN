# erp/web.py
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash

web_bp = Blueprint("web", __name__)

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

@web_bp.route("/")
def home():
    # Prefer your real pages present in the repo
    for candidate in (
        "auth/login.html",     # your real login
        "choose_login.html",   # also present
        "login.html",          # fallback
        "index.html",          # if you later add a root index
    ):
        try:
            return render_template(candidate)
        except Exception:
            continue
    current_app.logger.warning(
        "No suitable entry template found under templates/ or erp/templates/. Showing fallback."
    )
    return (
        "<h2>ERP-BERHAN is running.</h2>"
        "<p>Add <code>templates/auth/login.html</code> or <code>templates/choose_login.html</code> "
        "at repo root to render the UI here.</p>"
        "Health: <a href='/health'>/health</a>",
        200,
    )

@web_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "")
        pwd = request.form.get("password", "")
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session["user"] = user
            return redirect(url_for("web.dashboard"))
        flash("Invalid credentials", "error")
    # Prefer your real login template
    for candidate in ("auth/login.html", "login.html", "choose_login.html"):
        try:
            return render_template(candidate)
        except Exception:
            continue
    return (
        "<h3>Missing login templates.</h3>"
        "<p>Create <code>templates/auth/login.html</code> or "
        "<code>templates/login.html</code> at repo root.</p>",
        200,
    )

@web_bp.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("web.login"))
    for candidate in ("dashboard.html", "analytics/dashboard.html", "index.html"):
        try:
            return render_template(candidate)
        except Exception:
            continue
    return (
        "<h3>Missing dashboard template.</h3>"
        "<p>Try <code>templates/analytics/dashboard.html</code> or "
        "<code>templates/dashboard.html</code>.</p>",
        200,
    )
