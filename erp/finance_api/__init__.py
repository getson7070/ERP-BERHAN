from flask import Blueprint, jsonify
bp = Blueprint("finance_api", __name__)
@bp.get("/api/finance/ping")
def ping():
    return jsonify(status="ok", service="finance_api"), 200