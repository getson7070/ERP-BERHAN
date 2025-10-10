# erp/routes/main.py
from flask import Blueprint, render_template, request
from erp.security.device import read_device_id  # <-- from package, not from a shadowing file
from erp.models import User, DeviceAuthorization, Role

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("choose_login.html")

@main_bp.route("/choose_login")
def choose_login():
    device_id = read_device_id(request)
    client_on = True
    employee_on = False
    admin_on = False

    if device_id:
        # If ANY admin has this device, enable admin + employee.
        admin_allowed = (
            User.query
            .filter_by(role=Role.ADMIN, is_active=True)
            .join(DeviceAuthorization, User.id == DeviceAuthorization.user_id)
            .filter(DeviceAuthorization.device_id == device_id, DeviceAuthorization.allowed.is_(True))
            .first()
            is not None
        )
        employee_allowed = (
            User.query
            .filter_by(role=Role.EMPLOYEE, is_active=True)
            .join(DeviceAuthorization, User.id == DeviceAuthorization.user_id)
            .filter(DeviceAuthorization.device_id == device_id, DeviceAuthorization.allowed.is_(True))
            .first()
            is not None
        )

        if admin_allowed:
            admin_on = True
            employee_on = True
        elif employee_allowed:
            employee_on = True

    return render_template(
        "choose_login.html",
        client_on=client_on,
        employee_on=employee_on,
        admin_on=admin_on,
        device_id=device_id,
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
