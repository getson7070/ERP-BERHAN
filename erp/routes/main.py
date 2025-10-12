# erp/routes/main.py
from flask import Blueprint, render_template, request
from ..security_shim import read_device_id, compute_activation_for_device

main_bp = Blueprint("main", __name__)

@main_bp.get("/")
def index():
    # Just reuse the same view so "/" behaves like "/choose_login"
    return choose_login()

@main_bp.get("/choose_login")
def choose_login():
    device_id = read_device_id(request)
    activation = compute_activation_for_device(device_id)
    # Provide both names so the template works even if it still uses login_activation.
    return render_template(
        "choose_login.html",
        activation=activation,
        login_activation=activation,  # safe alias; remove once template is updated
    )

@main_bp.get("/help")
def help_page():
    return render_template("help.html")

@main_bp.get("/privacy")
def privacy_page():
    return render_template("privacy.html")

@main_bp.get("/feedback")
def feedback_page():
    return render_template("feedback.html")

# Do NOT define /health here since the app-level /health exists in create_app().
