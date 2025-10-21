from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)

@bp.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

@bp.get("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200

@bp.get("/readyz")
def readyz():
    return jsonify({"status": "ready"}), 200
