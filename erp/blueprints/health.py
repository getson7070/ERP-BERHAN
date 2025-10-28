from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)

@bp.get("/health/ready")
def ready():
    # Keep tiny; do not hit DB here unless you truly need it
    return jsonify(status="ready")

@bp.get("/health/live")
def live():
    return jsonify(status="live")
