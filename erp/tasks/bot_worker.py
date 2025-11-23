"""Celery worker for bot outbox processing with retries and idempotency."""
from __future__ import annotations

from celery import shared_task

from erp.extensions import db
from erp.models import (
    BotEvent,
    BotIdempotencyKey,
    BotJobOutbox,
    TelegramConversationState,
)
from erp.bots.nlp_intents import parse_intent
from erp.bots.dispatcher import dispatch
from erp.services.notification_service import send_email_fallback, send_telegram_message

MAX_RETRIES = 5


def _resolve_user(job: BotJobOutbox):
    try:
        from erp.models import User
    except Exception:
        return None
    if not hasattr(User, "telegram_chat_id"):
        return None
    return User.query.filter_by(org_id=job.org_id, telegram_chat_id=job.chat_id).first()


def _load_state(job: BotJobOutbox):
    return TelegramConversationState.query.filter_by(
        org_id=job.org_id, bot_name=job.bot_name, chat_id=job.chat_id
    ).first()


def _persist_state(job: BotJobOutbox, next_state: str | None, state_data: dict | None = None):
    state = _load_state(job)
    if not next_state:
        if state:
            db.session.delete(state)
        return
    if state is None:
        state = TelegramConversationState(
            org_id=job.org_id, bot_name=job.bot_name, chat_id=job.chat_id
        )
    state.state_key = next_state
    state.data_json = state_data or {}
    db.session.add(state)


@shared_task(bind=True, name="erp.tasks.bot.process_job")
def process_bot_job(self, job_id: int):
    job = BotJobOutbox.query.get(job_id)
    if not job or job.status in {"done", "processing"}:
        return {"status": "noop"}

    job.status = "processing"
    db.session.commit()

    existing = BotIdempotencyKey.query.filter_by(
        org_id=job.org_id, bot_name=job.bot_name, chat_id=job.chat_id, message_id=job.message_id
    ).first()
    if existing:
        job.status = "done"
        db.session.commit()
        return {"status": "duplicate_ignored"}

    try:
        intent = job.parsed_intent or parse_intent(job.raw_text or "")
        state = _load_state(job)
        ctx = {
            "user": _resolve_user(job),
            "raw_text": job.raw_text,
            "context": job.context_json or {},
            "state": getattr(state, "state_key", None),
            "state_data": getattr(state, "data_json", {}) if state else {},
        }
        response = dispatch(
            bot_name=job.bot_name,
            actor_id=getattr(ctx["user"], "id", None),
            chat_id=job.chat_id,
            message_id=job.message_id,
            raw_text=job.raw_text or "",
            intent=intent,
            ctx=ctx,
        )

        delivery = send_telegram_message(job.bot_name, job.chat_id, response, org_id=job.org_id)

        if isinstance(delivery, dict) and not delivery.get("ok", True):
            job.last_error = delivery.get("error")
            job.status = "failed"
            db.session.commit()
            return {"status": "delivery_failed", "error": delivery.get("error")}

        if "next_state" in response or response.get("clear_state"):
            _persist_state(
                job,
                None if response.get("clear_state") else response.get("next_state"),
                response.get("state_data") or {},
            )

        db.session.add(
            BotIdempotencyKey(
                org_id=job.org_id,
                bot_name=job.bot_name,
                chat_id=job.chat_id,
                message_id=job.message_id,
            )
        )
        job.status = "done"
        db.session.commit()
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - exercised in tests with retry
        db.session.add(
            BotEvent(
                org_id=job.org_id,
                bot_name=job.bot_name,
                event_type="error",
                actor_type="user",
                actor_id=None,
                chat_id=job.chat_id,
                message_id=job.message_id,
                payload_json={"error": str(exc), "retry": job.retry_count + 1},
                severity="critical",
            )
        )
        job.retry_count += 1
        job.last_error = str(exc)
        job.status = "failed" if job.retry_count >= MAX_RETRIES else "queued"
        db.session.commit()

        if job.retry_count < MAX_RETRIES:
            raise self.retry(countdown=2 ** job.retry_count)

        send_email_fallback(job, error=str(exc))
        return {"status": "fallback_sent"}
