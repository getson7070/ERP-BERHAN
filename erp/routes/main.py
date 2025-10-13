# erp/routes/main.py
import os
from flask import Blueprint, render_template, request

from ..security_shim import read_device_id, compute_activation_for_device

bp = Blueprint("main", __name__)

def _env_enabled_flags():
    return {
        "client": os.getenv("ENABLE_CLIENT_LOGIN", "false").lower() == "true",
        "employee": os.getenv("ENABLE_EMPLOYEE_LOGIN", "false").lower() == "true",
        "admin": os.getenv("ENABLE_ADMIN_LOGIN", "false").lower() == "true",
    }

@bp.route("/")
def index():
    return choose_login()

@bp.route("/choose_login")
def choose_login():
    # device-based activation + env toggles
    device_id = read_device_id(request)
    device_activation = compute_activation_for_device(device_id) or {}
    env_activation = _env_enabled_flags()
    activation = {
        "client": bool(device_activation.get("client", True) and env_activation["client"]),
        "employee": bool(device_activation.get("employee", False) and env_activation["employee"]),
        "admin": bool(device_activation.get("admin", False) and env_activation["admin"]),
    }
    return render_template("choose_login.html", activation=activation)

@bp.route("/help")
def help_page():
    return render_template("help.html")

@bp.route("/privacy")
def privacy_page():
    return render_template("privacy.html")

@bp.route("/feedback")
def feedback_page():
    return render_template("feedback.html")

@bp.route("/health")
def health():
    return ("OK", 200)
