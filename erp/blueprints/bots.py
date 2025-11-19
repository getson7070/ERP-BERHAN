"""Secure Slack bot endpoints."""
from __future__ import annotations

import os

from flask import Blueprint, current_app, jsonify, request

from erp.bot_security import verify_slack_request
from erp.extensions import limiter

bots_bp = Blueprint("bots", __name__, url_prefix="/bots")


def _require_slack_signature():
    if not verify_slack_request(request):
        current_app.logger.warning("Rejected Slack webhook due to invalid signature")
        return jsonify({"error": "invalid_signature"}), 401
    return None


@bots_bp.get("/slack/health")
def slack_health():
    """Report whether Slack automation credentials are configured."""

    ok = bool(
        os.environ.get("SLACK_BOT_TOKEN")
        and os.environ.get("SLACK_SIGNING_SECRET")
    )
    return jsonify(ok=ok, provider="slack", signature_required=True)


@bots_bp.post("/slack/echo")
@limiter.limit("30/minute")
def slack_echo():
    """Echo endpoint used by smoke tests and onboarding."""

    failure = _require_slack_signature()
    if failure is not None:
        return failure

    payload = request.get_json(silent=True) or {}
    if payload.get("type") == "url_verification":
        # Support Slack's challenge flow without exposing additional routes
        return jsonify({"challenge": payload.get("challenge")})
    return jsonify(received=payload, ok=True)


# alias for dynamic importer
bp = bots_bp


