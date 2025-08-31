"""Endpoints exposing integration hooks and tokens."""

from __future__ import annotations

import hmac
import hashlib
import os

from flask import Blueprint, current_app, request
from flask_security import auth_required, roles_required

from ...integrations import powerbi

bp = Blueprint("integration", __name__, url_prefix="/api")


@bp.post("/integrations/webhook")
@auth_required("token")
@roles_required("admin")
def integrations_webhook() -> tuple[dict, int]:
    """Accept signed webhook events from external systems."""
    secret = current_app.config.get(
        "WEBHOOK_SECRET", os.environ.get("WEBHOOK_SECRET", "")
    )
    body = request.get_data() or b""
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    provided = request.headers.get("X-Signature", "")
    if not hmac.compare_digest(expected, provided):
        return {"error": "invalid signature"}, 400
    data = request.get_json(silent=True) or {}
    event = data.get("event")
    payload = data.get("payload", {})
    if not isinstance(event, str) or not isinstance(payload, dict):
        return {"error": "invalid payload"}, 400
    # Event processing would occur here (queued or routed to connectors).
    return {"status": "received", "event": event}, 200


@bp.get("/integrations/powerbi-token")
@auth_required("token")
@roles_required("manager")
def integrations_powerbi_token() -> dict:
    """Expose a Power BI embed token for authorized dashboard rendering."""
    token = powerbi.get_embed_token()
    return {"token": token}
