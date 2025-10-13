# erp/routes/main.py
from __future__ import annotations

from flask import Blueprint, current_app, render_template, request

main_bp = Blueprint("main", __name__)


def _compute_activation():
    """
    Decide which login tiles should be enabled.
    Uses device-based helper if present, otherwise environment switches.
    """
    # Prefer the device-based shim if available
    try:
        from ..security_shim import read_device_id, compute_activation_for_device  # type: ignore

        device_id = read_device_id(request)
        act = compute_activation_for_device(device_id) or {}
    except Exception:
        act = {}

    # Environment switches (authoritative defaults)
    act.setdefault("client", bool(current_app.config.get("ENABLE_CLIENT_LOGIN", True)))
    act.setdefault("employee", bool(current_app.config.get("ENABLE_EMPLOYEE_LOGIN", False)))
    act.setdefault("admin", bool(current_app.config.get("ENABLE_ADMIN_LOGIN", False)))
    return act


@main_bp.route("/")
def index():
    return choose_login()


@main_bp.route("/choose_login")
def choose_login():
    activation = _compute_activation()
    return render_template(
        "choose_login.html",
        activation=activation,  # single source of truth in templates
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
