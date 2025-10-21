# erp/routes/webhooks.py
from __future__ import annotations

import hashlib
import hmac
import os

from flask import Blueprint, abort, current_app, jsonify, request

bp = Blueprint("webhooks", __name__)


def _get_signing_secret() -> str | None:
    """
    Resolve the webhook signing secret.

    In TESTING mode, prefer *only* app.config so that any machine/user env
    variables (e.g., WEBHOOK_SECRET) cannot interfere with tests. Outside
    TESTING, accept env or config.
    """
    app = current_app
    if app.config.get("TESTING"):
        return app.config.get("WEBHOOK_SIGNING_SECRET") or app.config.get("WEBHOOK_SECRET")

    return (
        os.getenv("WEBHOOK_SIGNING_SECRET")
        or app.config.get("WEBHOOK_SIGNING_SECRET")
        or app.config.get("WEBHOOK_SECRET")
        or os.getenv("WEBHOOK_SECRET")
    )


def _extract_signature() -> str | None:
    """
    Accept either raw hex in X-Signature or a GitHub-style header:
      X-Hub-Signature-256: sha256=<hex>
    """
    sig = request.headers.get("X-Signature") or request.headers.get("X-Hub-Signature-256")
    if not sig:
        return None
    if sig.startswith("sha256="):
        sig = sig.split("=", 1)[1]
    return sig


@bp.post("/api/webhook/test")
def webhook_test():
    # 1) Require secret to be configured (this must run BEFORE any other checks)
    secret = _get_signing_secret()
    if not secret:
        return jsonify({"error": "server not configured"}), 500

    # 2) Optional API token check
    api_token = current_app.config.get("API_TOKEN") or os.environ.get("API_TOKEN")
    auth = request.headers.get("Authorization", "")
    if api_token and auth != f"Bearer {api_token}":
        abort(401)

    # 3) Require signature header
    sig = _extract_signature()
    if not sig:
        return jsonify({"error": "missing signature"}), 401

    # 4) Validate HMAC-SHA256
    body = request.get_data() or b""
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac, sig):
        return jsonify({"error": "invalid signature"}), 401

    return jsonify({"ok": True}), 200


def init_app(app):
    """Register the webhooks blueprint on the given app."""
    if "webhooks" not in app.blueprints:
        app.register_blueprint(bp)
