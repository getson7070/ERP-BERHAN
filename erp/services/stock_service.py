from __future__ import annotations

import decimal
from typing import Optional, Tuple

from flask import current_app
from sqlalchemy.orm import Session
from erp.db import db
from erp.inventory.models import (
    Item,
    Warehouse,
    Lot,
    StockBalance,
    StockLedgerEntry,
    SerialNumber,  # Crucial for device/equipment tracking
)
from erp.models.user import User


class StockService:
    """Core stock management service."""

    @classmethod
    def adjust(
        cls,
        session: Session,
        item_id: int,
        warehouse_id: int,
        quantity: decimal.Decimal,
        reason: str,
        user: User,
        lot_id: Optional[int] = None,
        serial_number: Optional[str] = None,  # For devices/equipment
        batch_number: Optional[str] = None,  # For reagents (alias for Lot)
    ) -> Tuple[StockBalance, StockLedgerEntry]:
        """Adjust stock level and create ledger entry."""
        balance = cls._get_balance(session, item_id, warehouse_id)

        if quantity < 0 and balance.qty_on_hand + quantity < 0:
            if not current_app.config.get("ALLOW_NEGATIVE_STOCK"):
                raise ValueError("Cannot go negative without config flag")

        # Update balance
        balance.qty_on_hand += quantity

        # Create ledger entry with serial/lot
        ledger = StockLedgerEntry(
            item_id=item_id,
            warehouse_id=warehouse_id,
            lot_id=lot_id,
            serial_number=serial_number,  # Crucial for serialized items
            batch_number=batch_number,  # For reagents/batches
            quantity=quantity,
            reason=reason,
            created_by=user.id,
            reference_id=str(user.id),  # Simple ref for now
        )
        session.add(ledger)

        session.commit()

        return balance, ledger

    @classmethod
    def _get_balance(
        cls, session: Session, item_id: int, warehouse_id: int
    ) -> StockBalance:
        balance = (
            session.query(StockBalance)
            .filter_by(item_id=item_id, warehouse_id=warehouse_id)
            .first()
        )
        if not balance:
            # Create on demand
            balance = StockBalance(item_id=item_id, warehouse_id=warehouse_id)
            session.add(balance)
            session.commit()
        return balance


def get_available_stock(item_id: int, warehouse_id: int) -> decimal.Decimal:
    """Get current qty_on_hand for an item/warehouse combo."""
    balance = db.session.query(StockBalance).filter_by(
        item_id=item_id, warehouse_id=warehouse_id
    ).first()
    return balance.qty_on_hand if balance else decimal.Decimal("0")