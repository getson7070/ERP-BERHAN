"""Stock movement service enforcing inventory invariants.

This module centralizes stock mutations to keep balances and ledger entries
consistent. It offers both a low-level helper (`create_stock_movement`) and a
small convenience class (`StockService`) for common operations such as
incrementing, decrementing, and setting quantities.
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
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy import select
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


@dataclass
class StockMovementResult:
    """Return type for stock movement operations."""

    balance: StockBalance
    ledger: StockLedgerEntry

    balance: StockBalance
    ledger: StockLedgerEntry

def _to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))

def _to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _lock_or_create_balance(
    session: Session,
    *,
    org_id: int,
    item_id,
    warehouse_id,
) -> StockBalance:
    """Fetch the balance row for update, creating it if missing."""

    stmt = (
        select(StockBalance)
        .where(
            StockBalance.org_id == org_id,
            StockBalance.item_id == item_id,
            StockBalance.warehouse_id == warehouse_id,
        )
        .with_for_update()
    )

    balance = session.execute(stmt).scalar_one_or_none()
    if balance is None:
        balance = StockBalance(
            org_id=org_id,
            item_id=item_id,
            warehouse_id=warehouse_id,
            qty_on_hand=Decimal("0"),
            qty_reserved=Decimal("0"),
        )
        session.add(balance)
        session.flush()

    return balance


def _apply_movement(
    session: Session,
    *,
    org_id: int,
    item_id,
    warehouse_id,
    delta_qty: Decimal,
    tx_type: str,
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
    allow_negative: bool = False,
) -> StockMovementResult:
    """Apply a single stock movement inside an active transaction."""

    balance = _lock_or_create_balance(
        session,
        org_id=org_id,
        item_id=item_id,
        warehouse_id=warehouse_id,
    )

    current_qty = _to_decimal(balance.qty_on_hand or 0)
    new_qty = current_qty + _to_decimal(delta_qty)

    if new_qty < 0 and not allow_negative:
        raise ValueError(
            "Stock underflow: movement would drive qty_on_hand negative"
        )

    balance.qty_on_hand = new_qty

    return balance


def _apply_movement(
    session: Session,
    *,
    org_id: int,
    item_id,
    warehouse_id,
    delta_qty: Decimal,
    tx_type: str,
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
    allow_negative: bool = False,
) -> StockMovementResult:
    """Apply a single stock movement inside an active transaction."""

    balance = _lock_or_create_balance(
        session,
        org_id=org_id,
        item_id=item_id,
        warehouse_id=warehouse_id,
    )

    current_qty = _to_decimal(balance.qty_on_hand or 0)
    new_qty = current_qty + _to_decimal(delta_qty)

    if new_qty < 0 and not allow_negative:
        raise ValueError(
            "Stock underflow: movement would drive qty_on_hand negative"
        )

    balance.qty_on_hand = new_qty

def _apply_movement(
    session: Session,
    *,
    org_id: int,
    item_id,
    warehouse_id,
    delta_qty: Decimal,
    tx_type: str,
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
    allow_negative: bool = False,
) -> StockMovementResult:
    """Apply a single stock movement inside an active transaction."""

    balance = _lock_or_create_balance(
        session,
        org_id=org_id,
        item_id=item_id,
        warehouse_id=warehouse_id,
    )

    current_qty = _to_decimal(balance.qty_on_hand or 0)
    new_qty = current_qty + _to_decimal(delta_qty)

    if new_qty < 0 and not allow_negative:
        raise ValueError(
            "Stock underflow: movement would drive qty_on_hand negative"
        )

    balance.qty_on_hand = new_qty

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
        qty=_to_decimal(delta_qty),
        tx_type=tx_type,
        reference_type=reference_type,
        reference_id=reference_id,
    )
    session.add(ledger)
    session.flush()

    return StockMovementResult(balance=balance, ledger=ledger)


def create_stock_movement(
    *,
    org_id: int,
    item_id,
    warehouse_id,
    delta_qty,
    tx_type: str,
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
    allow_negative: bool = False,
    session: Optional[Session] = None,
) -> StockMovementResult:
    """Public entry point for atomic stock changes.

    Args:
        org_id: Organisation identifier for multi-tenant isolation.
        item_id: Item UUID.
        warehouse_id: Warehouse UUID.
        delta_qty: Quantity delta (+ for inbound, - for outbound).
        tx_type: Descriptive transaction type for auditability.
        reference_type: Optional reference entity type.
        reference_id: Optional reference entity identifier.
        allow_negative: Allow the resulting qty_on_hand to go negative.
        session: Optional SQLAlchemy session to use; defaults to `db.session`.
    """

    session = session or db.session
    delta_qty = _to_decimal(delta_qty)

    with session.begin_nested():
        result = _apply_movement(
            session,
            org_id=org_id,
            item_id=item_id,
            warehouse_id=warehouse_id,
            delta_qty=delta_qty,
            tx_type=tx_type,
            reference_type=reference_type,
            reference_id=reference_id,
            allow_negative=allow_negative,
        )

    return result


class StockService:
    """Convenience wrapper around stock movements for common flows."""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or db.session

    def increment(
        self,
        *,
        org_id: int,
        item_id,
        warehouse_id,
        qty,
        reason: str,
        ref_type: Optional[str] = None,
        ref_id: Optional[str] = None,
    ) -> StockMovementResult:
        return create_stock_movement(
            org_id=org_id,
            item_id=item_id,
            warehouse_id=warehouse_id,
            delta_qty=_to_decimal(qty),
            tx_type=reason,
            reference_type=ref_type,
            reference_id=ref_id,
            session=self.session,
        )

    def decrement(
        self,
        *,
        org_id: int,
        item_id,
        warehouse_id,
        qty,
        reason: str,
        ref_type: Optional[str] = None,
        ref_id: Optional[str] = None,
    ) -> StockMovementResult:
        qty = _to_decimal(qty)
        if qty <= 0:
            raise ValueError("Decrement qty must be positive")

        return create_stock_movement(
            org_id=org_id,
            item_id=item_id,
            warehouse_id=warehouse_id,
            delta_qty=-qty,
            tx_type=reason,
            reference_type=ref_type,
            reference_id=ref_id,
            allow_negative=False,
            session=self.session,
        )

    def set_quantity(
        self,
        *,
        org_id: int,
        item_id,
        warehouse_id,
        new_qty,
        reason: str,
        ref_type: Optional[str] = None,
        ref_id: Optional[str] = None,
    ) -> StockMovementResult:
        new_qty = _to_decimal(new_qty)
        if new_qty < 0:
            raise ValueError("new_qty cannot be negative")

        with self.session.begin_nested():
            balance = _lock_or_create_balance(
                self.session,
                org_id=org_id,
                item_id=item_id,
                warehouse_id=warehouse_id,
            )
            current_qty = _to_decimal(balance.qty_on_hand or 0)
            delta = new_qty - current_qty
            result = _apply_movement(
                self.session,
                org_id=org_id,
                item_id=item_id,
                warehouse_id=warehouse_id,
                delta_qty=delta,
                tx_type=reason,
                reference_type=ref_type,
                reference_id=ref_id,
                allow_negative=False,
            )

        return result

    def get_available_quantity(self, *, org_id: int, item_id, warehouse_id) -> Decimal:
        balance = (
            StockBalance.query.filter_by(
                org_id=org_id, item_id=item_id, warehouse_id=warehouse_id
            )
            .with_for_update(read=False)
            .one_or_none()
        )
        if balance is None:
            return Decimal("0")

        qty_on_hand = _to_decimal(balance.qty_on_hand or 0)
        reserved = _to_decimal(balance.qty_reserved or 0)
        return qty_on_hand - reserved
