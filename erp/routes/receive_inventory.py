from flask import Blueprint, render_template, request, jsonify, session, abort
from ..extensions import db
from ..inventory.models import Item
import secrets

bp = Blueprint("receive_inventory", __name__, url_prefix="/inventory/receive")

@bp.route("/", methods=["GET"])
def receive_form():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(16)
    return render_template("receive_inventory.html", csrf_token=session["csrf_token"])

def _exists_sku(value: str) -> bool:
    return db.session.query(Item.id).filter(Item.sku == value).first() is not None

@bp.route("/verify", methods=["POST"])
def verify_item():
    token = request.headers.get("X-CSRFToken")
    if token != session.get("csrf_token"):
        abort(400)
    code = (request.json or {}).get("code")
    if not code:
        abort(400)
    return jsonify({"valid": bool(_exists_sku(code))})

@bp.route("/verify_qr", methods=["POST"])
def verify_qr():
    token = request.headers.get("X-CSRFToken")
    if token != session.get("csrf_token"):
        abort(400)
    data = (request.json or {}).get("qr_data")
    if not data:
        abort(400)
    return jsonify({"valid": bool(_exists_sku(data))})


