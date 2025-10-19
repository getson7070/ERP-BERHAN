from flask import Blueprint, jsonify

bp = Blueprint("inventory_valuation", __name__)


@bp.get("/valuation/health")
def health():
    return jsonify({"ok": True})


