from __future__ import annotations

import hashlib
import hmac

from flask import Blueprint, abort, current_app, request

bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")


@bp.post("/notify")
def notify():
    payload = request.get_data() or b""
    sig = request.headers.get("X-Signature", "")
    secret = (current_app.config.get("WEBHOOK_SECRET") or "").encode()
    expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        abort(401)
    return "", 204
