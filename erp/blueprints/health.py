from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

@health_bp.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"ok": True})

bp = health_bp
