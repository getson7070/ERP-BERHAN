# erp/web.py
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash

web_bp = Blueprint("web", __name__)

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

@web_bp.route("/")
def home():
    # Prefer your real pages: root/templates/login.html or index.html
    for candidate in ("login.html", "index.html"):
        try:
            return render_template(candidate)
        except Exception:
            continue
    current_app.logger.warning(
        "No login.html or index.html found under either templates/ or erp/templates/. "
        "Showing fallback message."
    )
    return (
        "<h2>ERP-BERHAN is running.</h2>"
        "<p>Add <code>templates/login.html</code> or <code>templates/index.html</code> at repo root.</p>"
        "Health: <a href='/health'>/health</a>",
        200,
    )

@web_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        if u == ADMIN_USER and p == ADMIN_PASS:
            session["user"] = u
            return redirect(url_for("web.dashboard"))
        flash("Invalid credentials", "error")
    try:
        return render_template("login.html")
    except Exception:
        return (
            "<h3>Missing template: templates/login.html</h3>"
            "<p>Create it at repo root under <code>templates/login.html</code>.</p>",
            200,
        )

@web_bp.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("web.login"))
    for candidate in ("dashboard.html", "index.html"):
        try:
            return render_template(candidate)
        except Exception:
            continue
    return (
        "<h3>Missing template: templates/dashboard.html</h3>"
        "<p>Create it under <code>templates/dashboard.html</code>.</p>",
        200,
    )
