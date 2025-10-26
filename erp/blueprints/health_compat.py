from flask import Blueprint, jsonify

bp = Blueprint("health_compat", __name__)

@bp.get("/healthz")
def healthz():
    return jsonify(ok=True)

@bp.get("/health")
def health():
    return jsonify(ok=True)
