from flask import Blueprint, jsonify

finance_bp = Blueprint("finance", __name__, url_prefix="/finance")

@finance_bp.get("/health")
def health():
    return jsonify({"ok": True})

bp = finance_bp
