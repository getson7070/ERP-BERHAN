from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

@health_bp.get("/healthz")
@health_bp.get("/health")
def healthz():
    return jsonify(status="ok"), 200
