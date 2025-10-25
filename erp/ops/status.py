from flask import Blueprint, jsonify
bp = Blueprint("status", __name__)
@bp.get("/status")
def status():
    return jsonify({"ok": True}), 200
