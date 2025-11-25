"""Canonical stock movement service.

This module provides the ONLY place that is allowed to mutate inventory quantities.
All inventory-affecting modules (orders, returns, corrections, reservations, etc.)
must eventually call into this service instead of hand-modifying StockBalance.

Core invariants enforced here:

* qty_on_hand >= 0
* qty_reserved >= 0
* qty_reserved <= qty_on_hand
* qty_available = qty_on_hand - qty_reserved

Every change creates a StockLedgerEntry row so that stock is fully auditable.

Typical usage (inside an app / request / worker context):

    from erp.services.stock_service import StockDelta, apply_stock_delta

    delta = StockDelta(
        org_id=org.id,
        warehouse_id=warehouse.id,
        item_id=item.id,
        uom_name=item.uom_default,
        delta_on_hand=10,   # inbound
        delta_reserved=0,
        movement_type="inbound",
        document_type="purchase_order",
        document_id=str(po.id),
        actor_id=current_user.id if current_user else None,
        note="Initial GRN",
    )

    balance, ledger = apply_stock_delta(delta)

This service is intentionally low-level and does **not** know about business
concepts like “sales order” or “invoice”. Higher-level flows should build the
StockDelta object and delegate here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from erp.extensions import db
from erp.inventory.models import (
    Warehouse,
    Item,
    Lot,
    SerialNumber,
    StockBalance,
    StockLedgerEntry,
)


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------


@dataclass
class StockDelta:
    """Intent to change stock for a specific org/warehouse/item(+lot/serial).

    Two numbers drive everything:

    * delta_on_hand   – physical stock change (+ inbound, - outbound, 0 no change)
    * delta_reserved  – reservation change (+ reserve, - unreserve, 0 no change)

    Derived:

    * qty_available is always recomputed as on_hand - reserved.
    """

    org_id: int
    warehouse_id: int
    item_id: int

    # Optional granularity
    location_id: Optional[int] = None
    lot_id: Optional[int] = None
    serial_id: Optional[int] = None

    # Quantities
    uom_name: str = "unit"
    delta_on_hand: float = 0.0
    delta_reserved: float = 0.0

    # Classification / provenance
    movement_type: str = "adjustment"  # inbound | outbound | reserve | unreserve | correction | adjustment
    document_type: Optional[str] = None
    document_id: Optional[str] = None
    reason: Optional[str] = None
    source: Optional[str] = None  # e.g. "orders", "returns", "manual_adjustment"

    # Actor / audit
    actor_id: Optional[int] = None
    note: Optional[str] = None

    def classify_movement_type(self) -> str:
        """If caller didn't set movement_type explicitly, infer a sane label."""
        if self.movement_type and self.movement_type != "adjustment":
            return self.movement_type

        if self.delta_on_hand > 0 and self.delta_reserved == 0:
            return "inbound"
        if self.delta_on_hand < 0 and self.delta_reserved == 0:
            return "outbound"
        if self.delta_on_hand == 0 and self.delta_reserved > 0:
            return "reserve"
        if self.delta_on_hand == 0 and self.delta_reserved < 0:
            return "unreserve"

        # Mixed or unusual case – keep as generic adjustment
        return "adjustment"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _lock_or_create_balance(session: Session, delta: StockDelta) -> StockBalance:
    """Get the StockBalance row for this key, locking it for update.

    If it does not exist yet, create a zeroed row.

    This function must always be called inside a transaction.
    """
    stmt = (
        select(StockBalance)
        .where(
            StockBalance.org_id == delta.org_id,
            StockBalance.warehouse_id == delta.warehouse_id,
            StockBalance.item_id == delta.item_id,
            StockBalance.location_id.is_(delta.location_id)
            if delta.location_id is None
            else StockBalance.location_id == delta.location_id,
            StockBalance.lot_id.is_(delta.lot_id)
            if delta.lot_id is None
            else StockBalance.lot_id == delta.lot_id,
            StockBalance.serial_id.is_(delta.serial_id)
            if delta.serial_id is None
            else StockBalance.serial_id == delta.serial_id,
            StockBalance.uom_name == delta.uom_name,
        )
        .with_for_update()
    )

    balance: Optional[StockBalance] = session.execute(stmt).scalar_one_or_none()

    if balance is None:
        balance = StockBalance(
            org_id=delta.org_id,
            warehouse_id=delta.warehouse_id,
            item_id=delta.item_id,
            location_id=delta.location_id,
            lot_id=delta.lot_id,
            serial_id=delta.serial_id,
            uom_name=delta.uom_name,
            qty_on_hand=0,
            qty_reserved=0,
            qty_available=0,
        )
        session.add(balance)
        # Flush to assign an ID early and ensure row exists before we log ledger entry
        session.flush()

    return balance


def _apply_stock_delta_computed(session: Session, delta: StockDelta) -> Tuple[StockBalance, StockLedgerEntry]:
    """Core logic that mutates StockBalance and creates StockLedgerEntry.

    Assumes the caller already has an open transaction (db.session.begin or similar).
    """
    balance = _lock_or_create_balance(session, delta)

    old_on_hand = float(balance.qty_on_hand or 0)
    old_reserved = float(balance.qty_reserved or 0)

    new_on_hand = old_on_hand + float(delta.delta_on_hand or 0)
    new_reserved = old_reserved + float(delta.delta_reserved or 0)

    # --- Invariants ---------------------------------------------------------
    if new_on_hand < 0:
        raise ValueError(
            f"Stock underflow: on_hand would go negative for item_id={delta.item_id}, "
            f"warehouse_id={delta.warehouse_id}. Current={old_on_hand}, delta={delta.delta_on_hand}"
        )

    if new_reserved < 0:
        raise ValueError(
            f"Reserved underflow: reserved would go negative for item_id={delta.item_id}, "
            f"warehouse_id={delta.warehouse_id}. Current={old_reserved}, delta={delta.delta_reserved}"
        )

    if new_reserved > new_on_hand:
        raise ValueError(
            f"Reservation exceeds on-hand: reserved={new_reserved}, on_hand={new_on_hand} "
            f"(item_id={delta.item_id}, warehouse_id={delta.warehouse_id})"
        )

    new_available = new_on_hand - new_reserved

    # --- Update balance row -------------------------------------------------
    now = _now_utc()

    balance.qty_on_hand = new_on_hand
    balance.qty_reserved = new_reserved
    balance.qty_available = new_available
    balance.last_move_at = now

    # Update inbound / outbound timestamps
    if delta.delta_on_hand > 0:
        balance.last_inbound_at = now
    elif delta.delta_on_hand < 0:
        balance.last_outbound_at = now

    # Provenance
    balance.last_source = delta.source or delta.document_type or delta.movement_type
    if delta.document_type:
        balance.last_document = delta.document_type

    # --- Create ledger entry ------------------------------------------------
    movement_type = delta.classify_movement_type()

    ledger = StockLedgerEntry(
        org_id=delta.org_id,
        warehouse_id=delta.warehouse_id,
        item_id=delta.item_id,
        location_id=delta.location_id,
        lot_id=delta.lot_id,
        serial_id=delta.serial_id,
        uom_name=delta.uom_name,
        movement_type=movement_type,
        document_type=delta.document_type,
        document_id=delta.document_id,
        reason=delta.reason,
        source=delta.source,
        actor_id=delta.actor_id,
        note=delta.note,
        delta_qty=float(delta.delta_on_hand or 0),
        reserved_delta=float(delta.delta_reserved or 0),
        on_hand_after=new_on_hand,
        reserved_after=new_reserved,
        available_after=new_available,
        occurred_at=now,
    )

    session.add(ledger)
    session.flush()  # ensure ledger gets an ID before we return

    return balance, ledger


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def apply_stock_delta(delta: StockDelta, *, commit: bool = False) -> Tuple[StockBalance, StockLedgerEntry]:
    """Apply a stock change atomically and return (balance, ledger).

    * Uses SELECT ... FOR UPDATE to serialize concurrent adjustments.
    * Raises ValueError if invariants would be violated (negative stock, over-reservation).
    * Does NOT swallow IntegrityError — the caller should handle if needed.

    Args:
        delta: StockDelta request.
        commit: If True, commit the surrounding db.session when done.
                For most web flows, leave this False and let the caller manage
                the transaction boundary.

    Returns:
        (StockBalance, StockLedgerEntry)
    """
    session = db.session

    try:
        # nested transaction plays nicely whether or not a transaction is already open
        with session.begin_nested():
            balance, ledger = _apply_stock_delta_computed(session, delta)
    except IntegrityError:
        # we don't guess how to recover; bubble this up for the caller/logging
        session.rollback()
        raise

    if commit:
        session.commit()

    return balance, ledger


def inbound(
    *,
    org_id: int,
    warehouse_id: int,
    item_id: int,
    qty: float,
    uom_name: str = "unit",
    location_id: Optional[int] = None,
    lot_id: Optional[int] = None,
    serial_id: Optional[int] = None,
    document_type: Optional[str] = None,
    document_id: Optional[str] = None,
    actor_id: Optional[int] = None,
    reason: Optional[str] = None,
    source: Optional[str] = None,
    note: Optional[str] = None,
    commit: bool = False,
) -> Tuple[StockBalance, StockLedgerEntry]:
    """Convenience helper for inbound movements (receipts, returns to stock, etc.)."""
    delta = StockDelta(
        org_id=org_id,
        warehouse_id=warehouse_id,
        item_id=item_id,
        location_id=location_id,
        lot_id=lot_id,
        serial_id=serial_id,
        uom_name=uom_name,
        delta_on_hand=qty,
        delta_reserved=0.0,
        movement_type="inbound",
        document_type=document_type,
        document_id=document_id,
        actor_id=actor_id,
        reason=reason,
        source=source,
        note=note,
    )
    return apply_stock_delta(delta, commit=commit)


def outbound(
    *,
    org_id: int,
    warehouse_id: int,
    item_id: int,
    qty: float,
    uom_name: str = "unit",
    location_id: Optional[int] = None,
    lot_id: Optional[int] = None,
    serial_id: Optional[int] = None,
    document_type: Optional[str] = None,
    document_id: Optional[str] = None,
    actor_id: Optional[int] = None,
    reason: Optional[str] = None,
    source: Optional[str] = None,
    note: Optional[str] = None,
    commit: bool = False,
) -> Tuple[StockBalance, StockLedgerEntry]:
    """Convenience helper for outbound movements (picking, shipping, write-offs)."""
    if qty <= 0:
        raise ValueError("Outbound qty must be positive")

    delta = StockDelta(
        org_id=org_id,
        warehouse_id=warehouse_id,
        item_id=item_id,
        location_id=location_id,
        lot_id=lot_id,
        serial_id=serial_id,
        uom_name=uom_name,
        delta_on_hand=-qty,
        delta_reserved=0.0,
        movement_type="outbound",
        document_type=document_type,
        document_id=document_id,
        actor_id=actor_id,
        reason=reason,
        source=source,
        note=note,
    )
    return apply_stock_delta(delta, commit=commit)


def reserve(
    *,
    org_id: int,
    warehouse_id: int,
    item_id: int,
    qty: float,
    uom_name: str = "unit",
    location_id: Optional[int] = None,
    lot_id: Optional[int] = None,
    serial_id: Optional[int] = None,
    document_type: Optional[str] = None,
    document_id: Optional[str] = None,
    actor_id: Optional[int] = None,
    reason: Optional[str] = None,
    source: Optional[str] = None,
    note: Optional[str] = None,
    commit: bool = False,
) -> Tuple[StockBalance, StockLedgerEntry]:
    """Reserve stock (e.g. against a sales order)."""
    if qty <= 0:
        raise ValueError("Reserve qty must be positive")

    delta = StockDelta(
        org_id=org_id,
        warehouse_id=warehouse_id,
        item_id=item_id,
        location_id=location_id,
        lot_id=lot_id,
        serial_id=serial_id,
        uom_name=uom_name,
        delta_on_hand=0.0,
        delta_reserved=qty,
        movement_type="reserve",
        document_type=document_type,
        document_id=document_id,
        actor_id=actor_id,
        reason=reason,
        source=source,
        note=note,
    )
    return apply_stock_delta(delta, commit=commit)


def unreserve(
    *,
    org_id: int,
    warehouse_id: int,
    item_id: int,
    qty: float,
    uom_name: str = "unit",
    location_id: Optional[int] = None,
    lot_id: Optional[int] = None,
    serial_id: Optional[int] = None,
    document_type: Optional[str] = None,
    document_id: Optional[str] = None,
    actor_id: Optional[int] = None,
    reason: Optional[str] = None,
    source: Optional[str] = None,
    note: Optional[str] = None,
    commit: bool = False,
) -> Tuple[StockBalance, StockLedgerEntry]:
    """Release previously reserved stock."""
    if qty <= 0:
        raise ValueError("Unreserve qty must be positive")

    delta = StockDelta(
        org_id=org_id,
        warehouse_id=warehouse_id,
        item_id=item_id,
        location_id=location_id,
        lot_id=lot_id,
        serial_id=serial_id,
        uom_name=uom_name,
        delta_on_hand=0.0,
        delta_reserved=-qty,
        movement_type="unreserve",
        document_type=document_type,
        document_id=document_id,
        actor_id=actor_id,
        reason=reason,
        source=source,
        note=note,
    )
    return apply_stock_delta(delta, commit=commit)
