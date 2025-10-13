# erp/routes/main.py
from flask import Blueprint, render_template, request
from ..security_shim import read_device_id, compute_activation_for_device

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return choose_login()

@main_bp.route("/choose_login")
def choose_login():
    device_id = read_device_id(request)
    activation = compute_activation_for_device(device_id)
    return render_template(
        "choose_login.html",
        activation=activation,          # used in template
        login_activation=activation,    # backward-compat with older template
    )

@main_bp.route("/privacy")
def privacy_page():
    return render_template("privacy.html")

@main_bp.route("/help")
def help_page():
    return render_template("help.html")
