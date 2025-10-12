# erp/routes/main.py
from flask import Blueprint, render_template, request
from ..security.device import read_device_id, compute_activation_for_device

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return choose_login()

@bp.route("/choose_login")
def choose_login():
    # Compute activation per device to decide which tiles to show.
    device_id = read_device_id(request)
    activation = compute_activation_for
