from flask import Blueprint, jsonify

bp = Blueprint("status", __name__)

@bp.get("/healthz")
def healthz():
    return jsonify({"ok": True, "service": "erp"}), 200

@bp.get("/health")
def health():
    return jsonify({"ok": True, "service": "erp"}), 200
