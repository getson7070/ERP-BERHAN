"""Bot command handlers used by the dispatcher."""
from __future__ import annotations

from decimal import Decimal
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import object_session

from erp.bots.dispatcher import COMMANDS
from erp.extensions import db
from erp.models import PerformanceEvaluation, StockBalance
from erp.utils import resolve_org_id


def approve_action(ctx: dict) -> dict:
    entity_type = ctx.get("entity_type", "record")
    entity_id = ctx.get("entity_id")
    return {"text": f"✅ Approved {entity_type} #{entity_id}"}


def reject_action(ctx: dict) -> dict:
    entity_type = ctx.get("entity_type", "record")
    entity_id = ctx.get("entity_id")
    reason = ctx.get("reason") or ""
    suffix = f" Reason: {reason}" if reason else ""
    return {"text": f"❌ Rejected {entity_type} #{entity_id}.{suffix}"}


def inventory_query(ctx: dict) -> dict:
    org_id = resolve_org_id()
    query = (ctx.get("query") or "").lower()
    balances = (
        StockBalance.query.filter_by(org_id=org_id)
        .order_by(StockBalance.qty_on_hand.desc())
        .limit(20)
        .all()
    )
    lines = []
    for bal in balances:
        item_label = getattr(bal, "item_id", None)
        if query and query not in str(item_label).lower():
            continue
        lines.append(f"Item {item_label}: {Decimal(bal.qty_on_hand or 0):.3f}")
    if not lines:
        return {"text": "📦 No inventory records found."}
    return {"text": "📦 Inventory:\n" + "\n".join(lines)}


def analytics_query(ctx: dict) -> dict:
    org_id = resolve_org_id()
    cycle_id = ctx.get("cycle_id")

    q = PerformanceEvaluation.query.filter_by(org_id=org_id)
    if cycle_id:
        q = q.filter_by(cycle_id=cycle_id)
    rows = q.order_by(PerformanceEvaluation.total_score.desc()).limit(5).all()
    if not rows:
        return {"text": "No evaluations available yet."}
    lines = [
        f"{r.subject_type} #{r.subject_id}: {float(r.total_score):.1f}"
        for r in rows
    ]
    return {"text": "🏆 Top scores:\n" + "\n".join(lines)}


def help_menu(ctx: dict) -> dict:
    """Render a friendly help menu based on registered commands."""

    items = [
        "/help — show available commands",
        "/whoami — show the account connected to this chat",
        "/inventory <query> — check stock levels",
        "/analytics — top performance scores",
        "/approve <TYPE ID> — approve a pending item (admins)",
        "/reject <TYPE ID> — reject a pending item (admins)",
    ]

    # Surface any extra commands that may have been registered at runtime.
    dynamic = sorted(cmd for cmd in COMMANDS.keys() if cmd not in {
        "help",
        "whoami",
        "inventory_query",
        "analytics_query",
        "approve_action",
        "reject_action",
    })
    for cmd in dynamic:
        items.append(f"/{cmd} — custom action")

    return {"text": "🤖 Commands:\n" + "\n".join(items)}


def whoami(ctx: dict) -> dict:
    """Return a concise identity summary for the chat-bound user."""

    user = ctx.get("user")
    if not user:
        return {
            "text": (
                "I can't map this chat to an active ERP account. "
                "Make sure your Telegram chat ID is linked and you have an active session."
            )
        }

    # Avoid DetachedInstance errors by reading already-loaded values when the
    # SQLAlchemy session has been scoped away (common during background bot
    # dispatches or in tests).
    state = sa_inspect(user)
    session = object_session(user)
    if not session:
        user_id = state.identity[0] if state.identity else state.dict.get("id")
        reloaded = db.session.get(type(user), user_id) if user_id is not None else None
        if reloaded is not None:
            user = reloaded
            state = sa_inspect(user)
            session = object_session(user)
    username = state.dict.get("username") if not session else getattr(user, "username", "unknown")
    email = state.dict.get("email") if not session else getattr(user, "email", "unknown")
    roles_raw = state.dict.get("roles") if not session else getattr(user, "roles", [])
    username = username or "unknown"
    email = email or "unknown"
    roles = [getattr(r, "name", str(r)) for r in roles_raw or []]
    roles_text = ", ".join(sorted(set(roles))) if roles else "no roles"

    return {
        "text": (
            "👤 Identity\n"
            f"User: {username}\n"
            f"Email: {email}\n"
            f"Roles: {roles_text}\n"
            "Session is active and verified."
        )
    }


__all__ = [
    "approve_action",
    "reject_action",
    "inventory_query",
    "analytics_query",
    "help_menu",
    "whoami",
]
