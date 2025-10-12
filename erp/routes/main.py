# erp/routes/main.py
from flask import Blueprint, render_template, request
from ..security_shim import read_device_id, compute_activation_for_device

main_bp = Blueprint("main", __name__)

@main_bp.get("/")
def index():
    return choose_login()

@main_bp.get("/choose_login")
def choose_login():
    device_id = read_device_id(request)
    activation = compute_activation_for_device(device_id)
    # Keep legacy name too so older templates don't break
    return render_template("choose_login.html", activation=activation, login_activation=activation)

@main_bp.get("/help")
def help_page():
    return render_template("help.html")

@main_bp.get("/privacy")
def privacy_page():
    return render_template("privacy.html")

@main_bp.get("/feedback")
def feedback_page():
    return render_template("feedback.html")
