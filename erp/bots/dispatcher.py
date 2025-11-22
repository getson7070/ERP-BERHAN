"""Command dispatcher with basic role checks and bot event logging."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from erp.extensions import db
from erp.models import BotEvent
from erp.security import user_has_role
from erp.utils import resolve_org_id

Handler = Callable[[dict], Dict[str, Any]]


@dataclass
class CommandSpec:
    name: str
    required_role: str | None
    handler: Handler


COMMANDS: dict[str, CommandSpec] = {}


def register_command(name: str, handler: Handler, required_role: str | None = None) -> None:
    """Register a command that can be dispatched by bots."""

    COMMANDS[name] = CommandSpec(name=name, required_role=required_role, handler=handler)


def dispatch(
    *,
    bot_name: str,
    actor_id: int | None,
    chat_id: str,
    message_id: str,
    raw_text: str,
    intent: str | None,
    ctx: dict,
) -> dict:
    """Execute a bot command after permission and intent checks."""

    org_id = resolve_org_id()
    user = ctx.get("user")

    if not intent or intent not in COMMANDS:
        _event(org_id, bot_name, "command_parsed", actor_id, chat_id, message_id, {"intent": intent}, "warning")
        return {"text": "Sorry, I didn't understand. Type /help for commands."}

    spec = COMMANDS[intent]

    if spec.required_role and not user_has_role(user, spec.required_role):
        _event(org_id, bot_name, "permission_denied", actor_id, chat_id, message_id, {"intent": intent}, "warning")
        return {"text": f"You don't have permission for {intent}."}

    _event(org_id, bot_name, "command_executing", actor_id, chat_id, message_id, {"intent": intent}, "info")
    out = spec.handler(ctx)
    _event(org_id, bot_name, "command_executed", actor_id, chat_id, message_id, {"intent": intent}, "info")
    return out


def _event(org_id: int, bot_name: str, event_type: str, actor_id: int | None, chat_id: str, message_id: str,
           payload: dict, severity: str) -> None:
    db.session.add(
        BotEvent(
            org_id=org_id,
            bot_name=bot_name,
            event_type=event_type,
            actor_type="user",
            actor_id=actor_id,
            chat_id=str(chat_id),
            message_id=str(message_id),
            payload_json=payload or {},
            severity=severity,
        )
    )
    db.session.commit()
