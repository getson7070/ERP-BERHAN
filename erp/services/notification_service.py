"""Notification helpers for bot responses and fallbacks."""
from __future__ import annotations

from flask import current_app


def _logger():
    try:
        return current_app.logger
    except Exception:  # pragma: no cover - app context may be absent during tests
        return None


def send_telegram_message(bot_name: str, chat_id: str, payload: dict) -> None:
    """Send a message through Telegram if the transport is available."""
    logger = _logger()
    bots = (current_app.config.get("TELEGRAM_BOTS") if current_app else {}) or {}
    if not bots or bot_name not in bots:
        if logger:
            logger.info(
                "telegram_message_skipped",
                extra={"bot": bot_name, "chat_id": chat_id, "payload": payload},
            )
        return

    try:
        from erp.bots.telegram_client import telegram_send

        telegram_send(bot_name, chat_id, payload)
    except Exception as exc:  # pragma: no cover - network/env specific
        if logger:
            logger.warning(
                "telegram_send_failed",
                extra={"bot": bot_name, "chat_id": chat_id, "error": str(exc)},
            )


def send_email_fallback(job, error: str | None = None) -> None:
    """Email administrators when a bot job exhausts retries."""
    logger = _logger()
    recipients = ()
    try:
        recipients = tuple(current_app.config.get("BOT_FALLBACK_EMAILS", ()))
    except Exception:
        recipients = ()

    if recipients:
        try:
            from erp.emailer import send_email

            subject = f"Bot failure in {getattr(job, 'bot_name', 'bot')}"
            body = (
                f"Job {getattr(job, 'id', '?')} failed after retries.\n"
                f"Chat: {getattr(job, 'chat_id', '?')}\n"
                f"Message: {getattr(job, 'raw_text', '')}\n"
                f"Error: {error or 'unknown'}"
            )
            for rcpt in recipients:
                send_email(to=rcpt, subject=subject, body=body)
        except Exception as exc:  # pragma: no cover - depends on mail setup
            if logger:
                logger.warning(
                    "bot_fallback_email_failed",
                    extra={"error": str(exc), "job_id": getattr(job, "id", None)},
                )

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
