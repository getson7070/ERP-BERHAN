from flask import Blueprint, jsonify, request
import os

bots_bp = Blueprint("bots", __name__, url_prefix="/bots")

@bots_bp.get("/slack/health")
def slack_health():
    ok = bool(os.environ.get("SLACK_BOT_TOKEN")) and bool(os.environ.get("SLACK_SIGNING_SECRET"))
    return jsonify(ok=ok, provider="slack")

@bots_bp.post("/slack/echo")
def slack_echo():
    payload = request.get_json(silent=True) or {}
    return jsonify(received=payload)


