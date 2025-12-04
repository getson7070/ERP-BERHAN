"""Module: routes/main.py

Front-facing entry points for the ERP-BERHAN web UI:
- Root (/) landing
- Public help/privacy pages
- Simple feedback form
- Global /login shim that redirects to /auth/login
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user

# Keep both names for backwards compatibility:
# - some code may import `main_bp`
# - others import `bp`
main_bp = Blueprint("main", __name__)
bp = main_bp


@main_bp.route("/")
def index():
    """
    Root landing page.

    - If the user is authenticated → go straight to analytics dashboard.
    - If anonymous → show the login choice screen.
    """
    if current_user.is_authenticated:
        return redirect(url_for("analytics.dashboard_snapshot"))
    return render_template("choose_login.html")


@main_bp.route("/login")
def login_redirect():
    """
    Global /login entry point.

    - If the user is already authenticated → go to analytics dashboard.
    - If anonymous → redirect to the real auth blueprint login (/auth/login).
    This avoids 404s when the frontend, bookmarks, or humans hit /login directly.
    """
    if current_user.is_authenticated:
        return redirect(url_for("analytics.dashboard_snapshot"))
    return redirect(url_for("auth.login"))


@main_bp.route("/help")
def help_page():
    """Static help page with basic guidance and contacts."""
    return render_template("help.html")


@main_bp.route("/privacy")
def privacy_page():
    """Privacy policy page with basic configuration injected into the template."""
    privacy_config = {
        "company_name": "Berhan Pharma PLC",
        "officer_email": "info@berhanpharma.com",
        "last_update": "October 2025",
        "policy_summary": (
            "We value your privacy and protect your data under Ethiopian and "
            "international data protection principles."
        ),
    }
    return render_template("privacy.html", privacy_config=privacy_config)


@main_bp.route("/feedback/", methods=["GET", "POST"], strict_slashes=False)
def feedback_page():
    """
    Simple feedback form.

    In production this should store to DB or send email; for now we
    just flash a thank-you message and redirect back to the form.
    """
    if request.method == "POST":
        msg = request.form.get("feedback")
        # TODO: persist `msg` to database or send via email/notification
        flash("Thank you for your feedback!", "success")
        return redirect(url_for("main.feedback_page"))
    return render_template("feedback.html")


__all__ = ["bp", "index", "login_redirect", "help_page", "privacy_page", "feedback_page"]
