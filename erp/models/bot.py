"""Bot automation domain models (registry, events, outbox, idempotency)."""
from __future__ import annotations

from sqlalchemy import UniqueConstraint, func

from ..extensions import db


class BotCommandRegistry(db.Model):
    __tablename__ = "bot_command_registry"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    command = db.Column(db.String(64), nullable=False, index=True)
    description = db.Column(db.String(255), nullable=False)

    module = db.Column(db.String(64), nullable=False, index=True)
    required_role = db.Column(db.String(64), nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("org_id", "command", name="uq_bot_command"),
    )


class BotEvent(db.Model):
    __tablename__ = "bot_events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    bot_name = db.Column(db.String(64), nullable=False, index=True)
    event_type = db.Column(db.String(64), nullable=False, index=True)

    actor_type = db.Column(db.String(32), nullable=False, default="user", index=True)
    actor_id = db.Column(db.Integer, nullable=True, index=True)

    chat_id = db.Column(db.String(64), nullable=True, index=True)
    message_id = db.Column(db.String(64), nullable=True, index=True)

    payload_json = db.Column(
        db.JSON,
        nullable=False,
        default=dict,
        server_default=db.text("'{}'"),
    )
    severity = db.Column(db.String(16), nullable=False, default="info", index=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )


class BotJobOutbox(db.Model):
    __tablename__ = "bot_job_outbox"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    bot_name = db.Column(db.String(64), nullable=False, index=True)
    chat_id = db.Column(db.String(64), nullable=False, index=True)
    message_id = db.Column(db.String(64), nullable=False, index=True)

    raw_text = db.Column(db.Text, nullable=True)
    parsed_intent = db.Column(db.String(64), nullable=True, index=True)
    context_json = db.Column(
        db.JSON,
        nullable=False,
        default=dict,
        server_default=db.text("'{}'"),
    )

    status = db.Column(db.String(32), nullable=False, default="queued", index=True)
    retry_count = db.Column(db.Integer, nullable=False, default=0)
    last_error = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class TelegramConversationState(db.Model):
    """Lightweight conversation state for multi-step Telegram flows."""

    __tablename__ = "telegram_conversation_state"

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    org_id = db.Column(db.Integer, nullable=False, index=True)

    bot_name = db.Column(db.String(64), nullable=False, index=True)
    chat_id = db.Column(db.String(64), nullable=False, index=True)

    state_key = db.Column(db.String(64), nullable=False, index=True)
    data_json = db.Column(
        db.JSON,
        nullable=False,
        default=dict,
        server_default=db.text("'{}'"),
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("org_id", "bot_name", "chat_id", name="uq_tg_state"),
    )


class BotIdempotencyKey(db.Model):
    __tablename__ = "bot_idempotency_keys"

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    org_id = db.Column(db.Integer, nullable=False, index=True)

    bot_name = db.Column(db.String(64), nullable=False, index=True)
    chat_id = db.Column(db.String(64), nullable=False, index=True)
    message_id = db.Column(db.String(64), nullable=False, index=True)

    consumed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("org_id", "bot_name", "chat_id", "message_id", name="uq_bot_idem"),
    )
