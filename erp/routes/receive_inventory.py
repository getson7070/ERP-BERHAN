from flask import Blueprint, render_template, request, jsonify, abort
from erp.utils import login_required


# In a real implementation this would query the database for
# valid item identifiers. For the demo we keep an in-memory set.
EXPECTED_ITEM_IDS = {"ITEM123", "ITEM456"}

bp = Blueprint("receive_inventory", __name__, url_prefix="/inventory/receive")


@bp.route("/", methods=["GET"])
@login_required
def receive_form():
    return render_template("receive_inventory.html")


@bp.route("/verify", methods=["POST"])
@login_required
def verify_barcode():
    code = request.json.get("barcode")
    if not code:
        abort(400)
    return jsonify({"valid": code in EXPECTED_ITEM_IDS})


@bp.route("/verify_qr", methods=["POST"])
@login_required
def verify_qr():
    data = request.json.get("qr_data")
    if not data:
        abort(400)
    return jsonify({"valid": data in EXPECTED_ITEM_IDS})
