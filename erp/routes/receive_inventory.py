from flask import Blueprint, render_template, request, jsonify
from erp.utils import login_required

bp = Blueprint("receive_inventory", __name__, url_prefix="/inventory/receive")


@bp.route("/", methods=["GET"])
@login_required
def receive_form():
    return render_template("receive_inventory.html")


@bp.route("/verify", methods=["POST"])
@login_required
def verify_barcode():
    code = request.json.get("barcode", "")
    return jsonify({"valid": bool(code)})
