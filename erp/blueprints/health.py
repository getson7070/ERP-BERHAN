from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)

@bp.route("/healthz")
def healthz():
    return jsonify(status="ok"), 200

@bp.route("/readyz")
def readyz():
    return jsonify(status="ready"), 200
