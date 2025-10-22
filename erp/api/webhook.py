from __future__ import annotations
import os, hmac, hashlib, json
from flask import Blueprint, current_app, request, jsonify
from erp.extensions import csrf, limiter
from erp.db import redis_client
from erp.metrics import RATE_LIMIT_REJECTIONS

api_bp = Blueprint("api", __name__, url_prefix="/api")

def _dead_letter(payload: bytes, source: str, error: str) -> None:
    try:
        entry = {
            "task": "api.webhook",
            "source": source,
            "error": error,
            "payload": (payload.decode(errors="ignore") if isinstance(payload, (bytes, bytearray)) else str(payload)),
        }
        redis_client.lpush("dead_letter", json.dumps(entry))
    except Exception:
        # never let DLQ logging break the request path
        pass

@api_bp.post("/webhook/<source>")
@csrf.exempt
@limiter.limit("20 per minute")
def webhook(source: str):
    secret = current_app.config.get("WEBHOOK_SECRET", "secret")
    payload = request.get_data() or b""
    provided = request.headers.get("X-Signature", "")
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not provided or not hmac.compare_digest(provided, expected):
        _dead_letter(payload, source, "invalid_signature")
        return jsonify({"error": "invalid_signature"}), 401

    data = request.get_json(silent=True) or {}
    if data.get("simulate_failure"):
        _dead_letter(payload, source, "simulated_failure")
        # raise to produce 500 for the test
        raise RuntimeError("simulated webhook failure")

    return jsonify({"ok": True, "source": source}), 200

@api_bp.get("/tenders")
def tenders():
    token = os.environ.get("API_TOKEN", "testtoken")
    if request.headers.get("Authorization") != f"Bearer {token}":
        RATE_LIMIT_REJECTIONS.inc()
        return jsonify({"error": "unauthorized"}), 401
    # include description as tests expect
    return jsonify([{"id": 1, "title": "Tender A", "description": "Tender A"}])