from flask import Blueprint, jsonify
bp = Blueprint("integration", __name__, url_prefix="/integration")
@bp.get("/health")
def health():
    return jsonify({"ok": True})