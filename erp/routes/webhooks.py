<<<<<<< HEAD
from flask import Blueprint, current_app, request, abort
import hmac, hashlib, os
=======
﻿from __future__ import annotations
>>>>>>> 6232ca4 (Renormalize line endings)

<<<<<<< HEAD
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
=======
import hashlib
import hmac
import os
from flask import Blueprint, abort, current_app, jsonify, request

bp = Blueprint("webhooks", __name__, url_prefix="/api/webhook")
>>>>>>> a788d60 (routes/webhooks: clean rewrite with correct indentation and expected auth/HMAC behavior)

def _get_signing_secret():
    # Only the explicit key is considered (aligns with tests)
    return (
        current_app.config.get("WEBHOOK_SIGNING_SECRET")
        or os.getenv("WEBHOOK_SIGNING_SECRET")
    )

def _get_api_token():
    return current_app.config.get("API_TOKEN") or os.getenv("API_TOKEN")

@bp.post("/test")
def webhook_test():
    # 1) Server must be configured with a secret
    secret = _get_signing_secret()
    if not secret:
        current_app.logger.error("Webhook signing secret is not configured")
        return jsonify({"error": "server not configured"}), 500

    # 2) Optional bearer auth (enabled if API_TOKEN is set)
    required_token = _get_api_token()
    if required_token:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth.split(" ", 1)[1] != required_token:
            abort(401)

    # 3) Require signature header
    sig = (
        request.headers.get("X-Signature")
        or request.headers.get("X-Hub-Signature-256")
        or request.headers.get("X-Webhook-Signature")
    )
    if not sig:
        abort(401)

    # 4) Validate HMAC (constant-time)
    payload = request.get_data() or b""
    mac = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    expected = "sha256=" + mac
    if not hmac.compare_digest(sig, expected):
>>>>>>> 5d2708a (webhook: return 500 when signing secret is missing (before signature checks))
        abort(401)
<<<<<<< HEAD
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
=======

    # 5) All good
    return "", 204
>>>>>>> a788d60 (routes/webhooks: clean rewrite with correct indentation and expected auth/HMAC behavior)
