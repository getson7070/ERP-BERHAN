from flask import Blueprint, jsonify
bp = Blueprint("recall", __name__, url_prefix="/recall")
@bp.get("/health")
def health():
    return jsonify({"ok": True})