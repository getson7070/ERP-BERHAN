# erp/main.py

from flask import Blueprint

main_bp = Blueprint("main", __name__)


@main_bp.route("/dashboard")
def dashboard():
    """
    Simple dashboard placeholder.

    This gives you a stable target for redirects after login and
    a quick way to verify that authenticated routes are wired.
    """
    return "ERP-BERHAN dashboard", 200
