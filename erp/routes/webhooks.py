from __future__ import annotations

from flask import Blueprint, request, jsonify, current_app, abort
import os, hmac, hashlib

bp = Blueprint("webhooks", __name__)

@bp.post("/api/webhook/test")
def webhook_test():
    # Optional API token check
    api_token = (current_app.config.get("API_TOKEN") or os.environ.get("API_TOKEN"))
    auth = request.headers.get("Authorization", "")
    if api_token and auth != f"Bearer {api_token}":
        abort(401)

    # Require secret to be configured (env or config)
    secret = (
        os.getenv("WEBHOOK_SIGNING_SECRET")
        or current_app.config.get("WEBHOOK_SIGNING_SECRET")
        or current_app.config.get("WEBHOOK_SECRET")
        or os.getenv("WEBHOOK_SECRET")
    )
    if not secret:
        return jsonify({"error": "server not configured"}), 500

    # Accept either X-Signature (raw hex) or X-Hub-Signature-256 ("sha256=<hex>")
    sig = request.headers.get("X-Signature") or request.headers.get("X-Hub-Signature-256")
    if not sig:
        return jsonify({"error": "missing signature"}), 401
    if sig.startswith("sha256="):
        sig = sig.split("=", 1)[1]

    mac = hmac.new(secret.encode("utf-8"), request.get_data() or b"", hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac, sig):
        return jsonify({"error": "invalid signature"}), 401

    return jsonify({"ok": True}), 200

def init_app(app):
    """Register the webhooks blueprint on the given app."""
    app.register_blueprint(bp)