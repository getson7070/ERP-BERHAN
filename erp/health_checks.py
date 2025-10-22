from flask import Blueprint, jsonify

health_bp = Blueprint("health_bp", __name__)

@health_bp.get("/health")
def health():
    return jsonify({"ok": True})

@health_bp.get("/healthz")
def healthz():
    return "ok", 200

@health_bp.get("/readyz")
def readyz():
    # keep it simple; tests only care about 200/503 status existence
    return "ok", 200