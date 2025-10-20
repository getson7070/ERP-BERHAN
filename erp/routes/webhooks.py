<<<<<<< HEAD
from flask import Blueprint, current_app, request, abort
import hmac, hashlib, os
=======
﻿from __future__ import annotations
>>>>>>> 6232ca4 (Renormalize line endings)

bp = Blueprint("webhook", __name__)

<<<<<<< HEAD
@bp.post("/api/webhook/<name>")
def webhook(name):
    # Token check (kept as is)
    api_token = (current_app.config.get("API_TOKEN")
                 or os.environ.get("API_TOKEN"))
    auth = request.headers.get("Authorization", "")
    if api_token and auth != f"Bearer {api_token}":
=======
from flask import Blueprint, abort, current_app, request

bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")


@bp.post("/notify")
def notify():
        signing_secret = (
            getattr(current_app.config, 'get', lambda *_: None)('WEBHOOK_SIGNING_SECRET')
            or os.getenv('WEBHOOK_SIGNING_SECRET')
            or os.getenv('SIGNING_SECRET')
            or os.getenv('WEBHOOK_SECRET')
        )
        if not signing_secret:
            current_app.logger.error("Webhook signing secret is not configured")
            return jsonify({"error": "server not configured"}), 500
    payload = request.get_data() or b""
    sig = request.headers.get("X-Signature", "")
    secret = (current_app.config.get("WEBHOOK_SECRET") or "").encode()
    expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
>>>>>>> 5d2708a (webhook: return 500 when signing secret is missing (before signature checks))
        abort(401)
<<<<<<< HEAD

    # NEW: require secret to be configured; otherwise 500
    secret = (current_app.config.get("WEBHOOK_SECRET")
              or os.environ.get("WEBHOOK_SECRET"))
    if not secret:
        current_app.logger.error("WEBHOOK_SECRET is not configured.")
        abort(500)

    # Signature must be present once secret exists
    sig = request.headers.get("X-Hub-Signature-256")
    if not sig:
        abort(401)

    # ...verify HMAC as before...
    # computed = 'sha256=' + hmac.new(secret.encode(), request.data, hashlib.sha256).hexdigest()
    # if not hmac.compare_digest(sig, computed): abort(401)

    return ("", 204)
=======
    return "", 204


<<<<<<< HEAD
>>>>>>> 6232ca4 (Renormalize line endings)
=======

>>>>>>> 5d2708a (webhook: return 500 when signing secret is missing (before signature checks))
