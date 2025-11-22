"""Inventory background tasks for auto-reorder and expiry alerts."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from celery import shared_task

from erp.extensions import db
from erp.models import FinanceAuditLog
from erp.inventory.models import Lot, ReorderRule, StockBalance


@shared_task(name="erp.tasks.inventory.reorder_scan")
def reorder_scan() -> list[dict]:
    """Scan active reorder rules and emit suggestions when below thresholds."""

    rules = ReorderRule.query.filter(ReorderRule.is_active.is_(True)).all()
    suggestions: list[dict] = []

    for rule in rules:
        balance = StockBalance.query.filter_by(
            org_id=rule.org_id,
            item_id=rule.item_id,
            warehouse_id=rule.warehouse_id,
        ).first()
        on_hand = Decimal(balance.qty_on_hand) if balance else Decimal("0")

        if on_hand < (rule.min_qty or Decimal("0")):
            reorder_qty = rule.reorder_qty
            if reorder_qty is None:
                reorder_qty = (rule.max_qty or Decimal("0")) - on_hand

            suggestions.append(
                {
                    "org_id": rule.org_id,
                    "item_id": str(rule.item_id),
                    "warehouse_id": str(rule.warehouse_id),
                    "on_hand": float(on_hand),
                    "reorder_qty": float(reorder_qty),
                }
            )

            audit = FinanceAuditLog(
                org_id=rule.org_id,
                event_type="REORDER_SUGGESTION",
                entity_type="ITEM",
                entity_id=None,
                payload={
                    "item_id": str(rule.item_id),
                    "warehouse_id": str(rule.warehouse_id),
                    "on_hand": float(on_hand),
                    "reorder_qty": float(reorder_qty),
                },
            )
            db.session.add(audit)

    db.session.commit()
    return suggestions


@shared_task(name="erp.tasks.inventory.expiry_alerts")
def expiry_alerts(days: int = 90) -> int:
    """Log audit events for lots expiring within the provided window."""

    cutoff = date.today() + timedelta(days=days)
    lots = Lot.query.filter(
        Lot.is_active.is_(True),
        Lot.expiry.isnot(None),
        Lot.expiry <= cutoff,
    ).all()

    for lot in lots:
        audit = FinanceAuditLog(
            org_id=lot.org_id,
            event_type="LOT_EXPIRY_ALERT",
            entity_type="LOT",
            entity_id=None,
            payload={
                "item_id": str(lot.item_id),
                "lot_id": str(lot.id),
                "lot_number": lot.number,
                "expiry": lot.expiry.isoformat() if lot.expiry else None,
            },
        )
        db.session.add(audit)

    db.session.commit()
    return len(lots)
