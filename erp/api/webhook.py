# erp/api/webhook.py
from __future__ import annotations
import hmac, hashlib, json
from flask import Blueprint, current_app, request, jsonify
from erp.extensions import csrf, limiter
from db import redis_client  # re-exported from erp.db via root db.py

bp = Blueprint("webhook_api", __name__, url_prefix="/api/webhook")

def _dead_letter_handler(payload: bytes, source: str, error: str | None = None) -> None:
    data = {"task": "api.webhook", "source": source, "payload": payload.decode(errors="ignore")}
    if error:
        data["error"] = error
    if redis_client.is_real and redis_client.client:
        redis_client.client.lpush("dead_letter", json.dumps(data))

@bp.post("/<source>")
@csrf.exempt
@limiter.limit("20 per minute")
def receive_webhook(source: str):
    secret = current_app.config.get("WEBHOOK_SECRET")
    if not secret:
        return jsonify({"error": "secret_not_configured"}), 500
    payload = request.get_data() or b""
    sig = request.headers.get("X-Signature", "")
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not sig or not hmac.compare_digest(sig, expected):
        _dead_letter_handler(payload, source, "invalid_signature")
        return jsonify({"error": "invalid_signature"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify({"status": "ok", "source": source, "received": bool(data)}), 200
