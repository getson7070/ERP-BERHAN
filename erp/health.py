# erp/health.py
from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)

@bp.route("/healthz", methods=["GET"])
def healthz():
    return jsonify(status="ok"), 200
