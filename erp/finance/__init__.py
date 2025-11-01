from flask import Blueprint, jsonify
bp = Blueprint("finance", __name__)
@bp.get("/ping")
def ping():
    return jsonify(status="ok", service="finance"), 200