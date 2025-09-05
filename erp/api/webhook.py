from __future__ import annotations

import hmac
import hashlib
from flask import Blueprint, current_app, request, jsonify

from erp import csrf, limiter, _dead_letter_handler
from erp.routes.api import token_required
from erp.utils import idempotency_key_required

bp = Blueprint("webhook", __name__, url_prefix="/api/webhook")


@bp.post("/<source>")
@csrf.exempt
@token_required
@idempotency_key_required
@limiter.limit("20 per minute")
def receive_webhook(source: str):
    """Validate signed webhook payloads and enqueue failures."""
    secret = current_app.config.get("WEBHOOK_SECRET")
    if not secret:
        return jsonify({"error": "secret_not_configured"}), 500
    payload = request.get_data() or b""
    sig = request.headers.get("X-Signature", "")
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not sig or not hmac.compare_digest(sig, expected):
        return jsonify({"error": "invalid_signature"}), 401
    data = request.get_json(silent=True) or {}
    if data.get("simulate_failure"):
        _dead_letter_handler(
            sender=None,
            task_id=None,
            exception=Exception("simulate_failure"),
            args=(source,),
            kwargs=data,
        )
        return jsonify({"status": "queued"}), 500
    return jsonify({"status": "ok"})
