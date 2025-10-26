from flask import Blueprint, jsonify

finance_api_bp = Blueprint("finance_api", __name__, url_prefix="/api/finance")

@finance_api_bp.get("/health")
def health():
    return jsonify({"ok": True})

bp = finance_api_bp
