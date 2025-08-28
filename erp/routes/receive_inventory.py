from flask import Blueprint, render_template, request, jsonify, session, abort
from erp.utils import login_required
import secrets

# In a real implementation this would query the database for
# valid item identifiers. For the demo we keep an in-memory set.
EXPECTED_ITEM_IDS = {"ITEM123", "ITEM456"}

bp = Blueprint("receive_inventory", __name__, url_prefix="/inventory/receive")


@bp.route("/", methods=["GET"])
@login_required
def receive_form():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return render_template("receive_inventory.html", csrf_token=session["csrf_token"])


@bp.route("/verify", methods=["POST"])
@login_required
def verify_barcode():
    token = request.headers.get("X-CSRFToken")
    if token != session.get("csrf_token"):
        abort(400)
    code = request.json.get("barcode")
    if not code:
        abort(400)
    return jsonify({"valid": code in EXPECTED_ITEM_IDS})


@bp.route("/verify_qr", methods=["POST"])
@login_required
def verify_qr():
    token = request.headers.get("X-CSRFToken")
    if token != session.get("csrf_token"):
        abort(400)
    data = request.json.get("qr_data")
    if not data:
        abort(400)
    return jsonify({"valid": data in EXPECTED_ITEM_IDS})
