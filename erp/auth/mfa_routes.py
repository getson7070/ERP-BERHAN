from flask import Blueprint, jsonify

bp = Blueprint("mfa", __name__)

@bp.get("/ping")
def ping():
    return jsonify({"ok": True, "module": "mfa"}), 200
