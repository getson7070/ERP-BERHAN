# erp/routes/main.py

from __future__ import annotations

from flask import (
    Blueprint,
    render_template,
    make_response,
    request,
    redirect,
    url_for,
    flash,
)
from werkzeug.exceptions import BadRequest

# our device helpers
from erp.security.device import read_device_id

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    """
    Landing page -> choose_login with optional device cookie set.
    """
    resp = make_response(render_template("choose_login.html"))
    _maybe_set_device_cookie(resp)
    return resp

@main_bp.route("/choose_login")
def choose_login():
    """
    Shows the three tiles. Activation is computed in the app context_processor.
    Here we just set the cookie if we received a device id for the first time.
    """
    resp = make_response(render_template("choose_login.html"))
    _maybe_set_device_cookie(resp)
    return resp

@main_bp.route("/help")
def help_page():
    return render_template("help.html")

@main_bp.route("/privacy")
def privacy_page():
    return render_template("privacy.html")

@main_bp.route("/feedback", methods=["GET", "POST"])
def feedback_page():
    """
    Simple feedback endpoint.
    - GET renders the form
    - POST accepts a 'message' field and shows a thank-you (no email required)
    """
    if request.method == "POST":
        msg = (request.form.get("message") or "").strip()
        if not msg:
            raise BadRequest("Message is required.")
        # TODO: store msg (db, email, log). For now we just flash it.
        flash("Thanks for your feedback!", "success")
        return redirect(url_for("main.feedback_page"))
    return render_template("feedback.html")

@main_bp.route("/health")
def health():
    return ("OK", 200)

# -----------------------
# helpers
# -----------------------

def _maybe_set_device_cookie(resp):
    """
    Persist device id if provided via:
      - 'X-Device-ID' header, or
      - ?device= query param
    We set a cookie named 'device' for 180 days.
    """
    did = read_device_id(request)
    if did and not request.cookies.get("device"):
        resp.set_cookie(
            "device",
            did,
            max_age=60 * 60 * 24 * 180,  # 180 days
            secure=True,
            httponly=False,  # readable by JS if you ever need it in SPA
            samesite="Lax",
        )
