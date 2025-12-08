"""Telegram webhook ingestion feeding the bot outbox with scopes and consent checks."""
from __future__ import annotations

from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Iterable, Tuple

from flask import Blueprint, current_app, jsonify, request

from erp.bot_security import verify_telegram_secret
from erp.bots.nlp_intents import parse_intent
from erp.extensions import csrf, db, limiter
from erp.models import BotEvent, BotJobOutbox, User
from erp.models.security_ext import UserSession
from erp.utils import resolve_org_id
from erp.tasks.bot_worker import process_bot_job

bp = Blueprint("telegram_webhook", __name__, url_prefix="/telegram")


def _command_intent(text: str) -> Tuple[str | None, dict]:
    cmd = text.split()[0].lower()
    parts = text.split()
    ctx: dict = {}
    mapping = {
        "/help": "help",
        "/inventory": "inventory_query",
        "/approve": "approve_action",
        "/reject": "reject_action",
        "/analytics": "analytics_query",
        "/whoami": "whoami",
    }
    intent = mapping.get(cmd)
    if intent in {"approve_action", "reject_action"} and len(parts) >= 3:
        ctx["entity_type"] = parts[1].upper()
        try:
            ctx["entity_id"] = int(parts[2])
        except ValueError:
            ctx["entity_id"] = parts[2]
    if intent == "inventory_query" and len(parts) > 1:
        ctx["query"] = " ".join(parts[1:])
    return intent, ctx


def _allowed_for_bot(bot_name: str, user_roles: tuple[str, ...] | None) -> bool:
    scopes = current_app.config.get("TELEGRAM_BOT_SCOPES", {}) if current_app else {}
    allowed_roles = tuple(scopes.get(bot_name, {}).get("allowed_roles", []))
    if not allowed_roles:
        return True
    roles = user_roles or ()
    return any(r in allowed_roles for r in roles)


def _allowed_chat(bot_name: str, chat_id: str) -> bool:
    allowed_map = current_app.config.get("TELEGRAM_ALLOWED_CHAT_IDS", {}) if current_app else {}
    if not allowed_map:
        return True
    specific: Iterable[str] = allowed_map.get(bot_name, []) or []
    wildcard: Iterable[str] = allowed_map.get("*", []) or []
    allowed = {str(cid) for cid in list(specific) + list(wildcard)}
    if not allowed:
        return True
    return str(chat_id) in allowed


def _resolve_user(org_id: int, chat_id: str):
    if not hasattr(User, "telegram_chat_id"):
        return None
    return User.query.filter_by(org_id=org_id, telegram_chat_id=chat_id).first()


def _has_active_session(org_id: int, user_id: int) -> bool:
    require_session = bool(
        current_app.config.get("TELEGRAM_REQUIRE_ACTIVE_SESSION", False)
        if current_app
        else False
    )
    if not require_session:
        return True

    max_age = int(current_app.config.get("TELEGRAM_SESSION_MAX_AGE_SECONDS", 7200))
    cutoff = datetime.utcnow() - timedelta(seconds=max_age)
    session = (
        UserSession.query.filter_by(org_id=org_id, user_id=user_id)
        .filter(UserSession.revoked_at.is_(None))
        .filter(UserSession.last_seen_at >= cutoff)
        .first()
    )
    if not session:
        current_app.logger.warning(
            "Blocking Telegram webhook due to missing active user session",
            extra={"org_id": org_id, "user_id": user_id},
        )
    return bool(session)


@bp.post("/<bot_name>/webhook")
@csrf.exempt
@limiter.limit("60/minute")
def telegram_webhook(bot_name: str):
    org_id = resolve_org_id()

    require_secret = bool(
        (current_app.config.get("TELEGRAM_WEBHOOK_REQUIRE_SECRET", True)) if current_app else True
    )
    secret = current_app.config.get("TELEGRAM_WEBHOOK_SECRET") if current_app else None
    if require_secret and not secret:
        current_app.logger.warning(
            "Blocking Telegram webhook because TELEGRAM_WEBHOOK_SECRET is not configured",
            extra={"bot_name": bot_name, "org_id": org_id},
        )
        return (
            jsonify({"status": "misconfigured", "message": "Webhook secret required"}),
            HTTPStatus.SERVICE_UNAVAILABLE,
        )
    if (secret or require_secret) and not verify_telegram_secret(request, require_config=require_secret):
        current_app.logger.warning(
            "Telegram webhook rejected due to invalid secret",
            extra={"bot_name": bot_name, "org_id": org_id},
        )
        return jsonify({"status": "unauthorized"}), HTTPStatus.UNAUTHORIZED

    bots = (current_app.config.get("TELEGRAM_BOTS") if current_app else {}) or {}
    if bots and bot_name not in bots:
        return jsonify({"status": "unknown_bot"}), HTTPStatus.NOT_FOUND

    update = request.get_json(silent=True) or {}
    msg = update.get("message") or update.get("edited_message")
    cbq = update.get("callback_query")

    if not msg and not cbq:
        return jsonify({"status": "ignored"}), HTTPStatus.OK

    if msg:
        chat_id = str(msg["chat"]["id"])
        message_id = str(msg.get("message_id"))
        text = (msg.get("text") or "").strip()

        user = _resolve_user(org_id, chat_id)
        if not user:
            return jsonify({"status": "unknown_chat"}), HTTPStatus.FORBIDDEN

        if not _allowed_chat(bot_name, chat_id):
            return jsonify({"status": "chat_not_allowlisted"}), HTTPStatus.FORBIDDEN

        roles = tuple(getattr(user, "roles", []) or [])
        if not _allowed_for_bot(bot_name, roles):
            return jsonify({"status": "blocked_by_scope"}), HTTPStatus.FORBIDDEN

        if not _has_active_session(org_id, user.id):
            return jsonify({"status": "session_required"}), HTTPStatus.UNAUTHORIZED

        db.session.add(
            BotEvent(
                org_id=org_id,
                bot_name=bot_name,
                event_type="message_received",
                actor_id=user.id,
                chat_id=chat_id,
                message_id=message_id,
                payload_json={"text": text},
            )
        )

        intent_ctx = {}
        intent = None
        if text.startswith("/"):
            intent, intent_ctx = _command_intent(text)
        if not intent:
            intent = parse_intent(text)

        job = BotJobOutbox(
            org_id=org_id,
            bot_name=bot_name,
            chat_id=chat_id,
            message_id=message_id,
            raw_text=text,
            parsed_intent=intent,
            context_json=intent_ctx,
            status="queued",
        )
        db.session.add(job)
        db.session.commit()

        try:
            process_bot_job.delay(job.id)
        except Exception:
            process_bot_job.run(job.id)
        return jsonify({"status": "queued"}), HTTPStatus.OK

    if cbq:
        chat_id = str(cbq["message"]["chat"]["id"])
        message_id = str(cbq["message"]["message_id"])
        data = cbq.get("data", "")

        user = _resolve_user(org_id, chat_id)
        if not user:
            return jsonify({"status": "unknown_chat"}), HTTPStatus.FORBIDDEN

        if not _allowed_chat(bot_name, chat_id):
            return jsonify({"status": "chat_not_allowlisted"}), HTTPStatus.FORBIDDEN

        roles = tuple(getattr(user, "roles", []) or [])
        if not _allowed_for_bot(bot_name, roles):
            return jsonify({"status": "blocked_by_scope"}), HTTPStatus.FORBIDDEN

        if not _has_active_session(org_id, user.id):
            return jsonify({"status": "session_required"}), HTTPStatus.UNAUTHORIZED

        db.session.add(
            BotEvent(
                org_id=org_id,
                bot_name=bot_name,
                event_type="callback_received",
                actor_id=user.id,
                chat_id=chat_id,
                message_id=message_id,
                payload_json={"data": data},
            )
        )
        db.session.commit()

        intent, ctx_patch = _intent_from_callback(data)
        job = BotJobOutbox(
            org_id=org_id,
            bot_name=bot_name,
            chat_id=chat_id,
            message_id=message_id,
            raw_text=f"[callback]{data}",
            parsed_intent=intent,
            context_json=ctx_patch,
            status="queued",
        )
        db.session.add(job)
        db.session.commit()

        try:
            process_bot_job.delay(job.id)
        except Exception:
            process_bot_job.run(job.id)
        return jsonify({"status": "queued"}), HTTPStatus.OK

    return jsonify({"status": "ignored"}), HTTPStatus.OK


@bp.post("/webhook")
@limiter.limit("60/minute")
def default_webhook():
    default_bot = current_app.config.get("TELEGRAM_DEFAULT_BOT", "erpbot")
    return telegram_webhook(default_bot)


def _intent_from_callback(data: str):
    parts = (data or "").split(":")
    if len(parts) >= 3:
        verb, et, eid = parts[0], parts[1], parts[2]
        ctx = {"entity_type": et, "entity_id": eid}
        if verb == "approve":
            return "approve_action", ctx
        if verb == "reject":
            return "reject_action", ctx
    return None, {}
