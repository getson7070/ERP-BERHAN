# erp/web.py
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash

web_bp = Blueprint("web", __name__)

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

@web_bp.route("/")
def home():
    for candidate in ("auth/login.html", "choose_login.html", "login.html", "index.html"):
        try:
            return render_template(candidate)
        except Exception:
            continue
    current_app.logger.warning("No entry template found under templates/ or erp/templates/.")
    return (
        "<h2>ERP-BERHAN is running.</h2>"
        "<p>Add <code>templates/auth/login.html</code> or <code>templates/choose_login.html</code> at repo root.</p>"
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
    for candidate in ("auth/login.html", "login.html", "choose_login.html"):
        try:
            return render_template(candidate)
        except Exception:
            continue
    return "<h3>Missing login templates.</h3>", 200

@web_bp.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("web.login"))
    for candidate in ("dashboard.html", "analytics/dashboard.html", "index.html"):
        try:
            return render_template(candidate)
        except Exception:
            continue
    return "<h3>Missing dashboard template.</h3>", 200
