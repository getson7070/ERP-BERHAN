# erp/routes/main.py
from flask import Blueprint, redirect, url_for, render_template, jsonify
from flask_login import current_user

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return redirect(url_for("main.choose_login"))

@main_bp.route("/choose_login")
def choose_login():
    show_admin = current_user.is_authenticated and getattr(current_user, "role", None) in {"admin", "superadmin"}
    show_employee = current_user.is_authenticated and getattr(current_user, "role", None) in {"employee", "admin", "superadmin"}
    # Client is always public
    return render_template("choose_login.html", show_admin=show_admin, show_employee=show_employee)

# ---- Static info pages (avoid 404) ----
@main_bp.route("/help")
def help_page():
    return render_template("info/help.html")

@main_bp.route("/privacy")
def privacy_page():
    return render_template("info/privacy.html")

@main_bp.route("/feedback", methods=["GET"])
def feedback_page():
    return render_template("info/feedback.html")

# ---- Health check (200 OK) ----
@main_bp.route("/health")
def health():
    return jsonify(status="ok"), 200
