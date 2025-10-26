from flask import Blueprint, jsonify

recall_bp = Blueprint("recall", __name__, url_prefix="/recall")

@recall_bp.get("/health")
def health():
    return jsonify({"ok": True})

bp = recall_bp
