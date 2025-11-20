"""Concurrency-safe helpers for stock adjustments and ledger writes."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Query

from erp.extensions import db
from erp.inventory.models import StockBalance, StockLedgerEntry


def _get_existing_by_idempotency(org_id: int, idempotency_key: Optional[str]) -> Optional[StockLedgerEntry]:
    if not idempotency_key:
        return None
    return (
        StockLedgerEntry.query.filter_by(org_id=org_id, idempotency_key=idempotency_key)
        .with_for_update(nowait=False)
        .first()
    )


def adjust_stock(
    *,
    org_id: int,
    item_id,
    warehouse_id,
    qty_delta: Decimal,
    location_id=None,
    lot_id=None,
    serial_id=None,
    tx_type: str,
    reference_type: str | None = None,
    reference_id=None,
    idempotency_key: str | None = None,
    unit_cost: Decimal | None = None,
    created_by_id: int | None = None,
) -> StockLedgerEntry:
    """Apply a stock movement with row locks and ledger recording.

    - Guarded by idempotency_key when provided
    - Uses SELECT ... FOR UPDATE on StockBalance to prevent races
    - Blocks negative inventory unless explicitly handled by the caller
    """

    existing = _get_existing_by_idempotency(org_id, idempotency_key)
    if existing:
        return existing

    balance: Query[StockBalance] = (
        StockBalance.query.filter_by(
            org_id=org_id,
            item_id=item_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            lot_id=lot_id,
        )
        .with_for_update()
    )

    bal = balance.first()
    if not bal:
        bal = StockBalance(
            org_id=org_id,
            item_id=item_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            lot_id=lot_id,
            qty_on_hand=Decimal("0"),
            qty_reserved=Decimal("0"),
        )
        db.session.add(bal)
        db.session.flush()

    new_qty = Decimal(bal.qty_on_hand or 0) + Decimal(qty_delta)
    if new_qty < 0:
        raise ValueError("Negative stock not allowed")

    bal.qty_on_hand = new_qty

    ledger = StockLedgerEntry(
        org_id=org_id,
        item_id=item_id,
        warehouse_id=warehouse_id,
        location_id=location_id,
        lot_id=lot_id,
        serial_id=serial_id,
        qty=qty_delta,
        rate=unit_cost or Decimal("0"),
        value=(unit_cost or Decimal("0")) * Decimal(qty_delta),
        tx_type=tx_type,
        reference_type=reference_type,
        reference_id=reference_id,
        idempotency_key=idempotency_key,
        created_by_id=created_by_id,
    )
    db.session.add(ledger)
    return ledger
