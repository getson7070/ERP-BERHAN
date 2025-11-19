"""Shared helpers for validating bot/webhook authenticity."""
from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

from flask import Request, current_app

_SLACK_VERSION = "v0"


def _constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def verify_slack_request(request: Request, tolerance_seconds: int = 300) -> bool:
    """Return True if the Slack signature and timestamp validate."""

    secret = current_app.config.get("SLACK_SIGNING_SECRET")
    if not secret:
        return False

    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature") or ""
    if not timestamp or not signature:
        return False

    try:
        ts_int = int(timestamp)
    except (TypeError, ValueError):
        return False

    if abs(time.time() - ts_int) > tolerance_seconds:
        return False

    body = request.get_data(cache=True, as_text=True) or ""
    basestring = f"{_SLACK_VERSION}:{timestamp}:{body}"
    expected = hmac.new(
        secret.encode("utf-8"), basestring.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    signed = signature.replace(f"{_SLACK_VERSION}=", "")
    return _constant_time_equals(expected, signed)


def verify_telegram_secret(request: Request) -> bool:
    """Validate Telegram webhook secret token (if configured)."""

    secret = current_app.config.get("TELEGRAM_WEBHOOK_SECRET")
    if not secret:
        return False
    provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    return _constant_time_equals(secret, provided)


def describe_machine_identity(source: str) -> dict[str, Any]:
    """Return a canonical identity payload for machine-to-machine hooks."""

    roles = current_app.config.get("AUTOMATION_MACHINE_ROLES") or ("automation",)
    return {"id": source, "roles": roles}
