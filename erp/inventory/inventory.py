from flask import Blueprint, jsonify

bp = Blueprint("inventory", __name__)


@bp.get("/inventory/health")
def health():
    return jsonify({"ok": True})


