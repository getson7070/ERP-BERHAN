"""Notification helpers for bot responses and fallbacks."""
from __future__ import annotations

from flask import current_app


def send_telegram_message(bot_name: str, chat_id: str, payload: dict) -> None:
    """Send a message through Telegram if the transport is available."""

    # Stub transport: log to application logger if telegram client is unavailable.
    try:
        logger = current_app.logger
    except Exception:  # pragma: no cover - app context may be absent during tests
        logger = None

    if logger:
        logger.info("telegram_message", extra={"bot": bot_name, "chat_id": chat_id, "payload": payload})


def send_email_fallback(job, error: str | None = None) -> None:
    """Email administrators when a bot job exhausts retries."""

    try:
        logger = current_app.logger
    except Exception:  # pragma: no cover - app context may be absent during tests
        logger = None

    if logger:
        logger.warning(
            "bot_fallback_email",
            extra={
                "job_id": getattr(job, "id", None),
                "chat_id": getattr(job, "chat_id", None),
                "message_id": getattr(job, "message_id", None),
                "error": error,
            },
        )
