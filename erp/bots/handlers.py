"""Bot command handlers used by the dispatcher."""
from __future__ import annotations

from decimal import Decimal
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


__all__ = [
    "approve_action",
    "reject_action",
    "inventory_query",
    "analytics_query",
]
