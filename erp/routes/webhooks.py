from flask import Blueprint, current_app, request, abort
import hmac, hashlib, os

bp = Blueprint("webhook", __name__)

@bp.post("/api/webhook/<name>")
def webhook(name):
    # Token check (kept as is)
    api_token = (current_app.config.get("API_TOKEN")
                 or os.environ.get("API_TOKEN"))
    auth = request.headers.get("Authorization", "")
    if api_token and auth != f"Bearer {api_token}":
        abort(401)

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
