# erp/routes/main.py
from flask import Blueprint, render_template, request, current_app, redirect, url_for
from ..security_shim import read_device_id, compute_activation_for_device

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    # Honor configured entry template (choose_login by default)
    return redirect(url_for("main.choose_login"))

@main_bp.route("/choose_login")
def choose_login():
    device_id = read_device_id(request)
    activation = compute_activation_for_device(device_id)
    return render_template(
        current_app.config.get("ENTRY_TEMPLATE", "choose_login.html"),
        activation=activation,
        login_activation=activation,  # legacy template compatibility
    )

@main_bp.route("/help")
def help_page():
    return render_template("help.html")

@main_bp.route("/privacy")
def privacy_page():
    return render_template("privacy.html")

@main_bp.route("/feedback")
def feedback_page():
    return render_template("feedback.html")

@main_bp.route("/health")
def health():
    return ("OK", 200)
