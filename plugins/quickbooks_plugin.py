from flask import Blueprint, jsonify

bp = Blueprint("quickbooks", __name__, url_prefix="/quickbooks")


@bp.route("/ping")
def ping():
    return jsonify({"status": "ok"})


