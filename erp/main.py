# erp/main.py

from erp.routes.main import main_bp as bp


@bp.route("/dashboard")
def dashboard():
    """
    Simple dashboard placeholder.

    This gives you a stable target for redirects after login and
    a quick way to verify that authenticated routes are wired.
    """
    return "ERP-BERHAN dashboard", 200


__all__ = ["bp", "dashboard"]
