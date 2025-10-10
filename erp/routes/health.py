from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

@health_bp.get("/health")
def health():
    return jsonify(status="ok")

@health_bp.get("/api/health")
def api_health():
    return jsonify(status="ok", api=True)
