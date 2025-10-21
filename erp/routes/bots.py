from flask import Blueprint, jsonify
bp = Blueprint("bots", __name__, url_prefix="/bots")
@bp.get("/slack/health")
def slack_health():
    return jsonify({"ok": True})