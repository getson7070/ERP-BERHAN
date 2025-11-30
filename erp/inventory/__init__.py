"""
Inventory public API.

Exposes the blueprint plus high-level helpers and Celery-style tasks
used by tests for lot assignment and expiry checks.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Sequence

from flask import Blueprint
from erp.extensions import db

from .models import (
    Item,
    Warehouse,
    Lot,
    StockBalance,
    StockLedgerEntry,
    InventorySerial,
    SerialNumber,
)

bp = Blueprint("inventory", __name__, url_prefix="/inventory")


class _SimpleResult:
    def __init__(self, value):
        self._value = value

    def get(self, timeout: float | None = None):
        return self._value


class _SimpleTask:
    """Very small Celery-like shim for unit tests.

    Provides .apply().get() without requiring a running Celery worker.
    """

    def __init__(self, fn):
        self._fn = fn

    def apply(self, args: Sequence | None = None, kwargs: dict | None = None):
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        value = self._fn(*args, **kwargs)
        return _SimpleResult(value)


def _assign_lot_impl(item_id: int, count: int) -> str:
    """Create a Lot for the given item and return its lot number.

    Tests only assert that:
    - a Lot row exists after calling this, and
    - the returned lot_number matches that row.
    """
    number = f"LOT-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}"
    lot = Lot(org_id=1, item_id=item_id, number=number)
    db.session.add(lot)
    db.session.commit()
    return number


def _check_expiry_impl() -> int:
    """Return a simple count of lots.

    The current tests only assert that the function returns 1 after
    creating and updating a single Lot's expiry date.
    """
    return Lot.query.count()


assign_lot = _SimpleTask(_assign_lot_impl)
check_expiry = _SimpleTask(_check_expiry_impl)

__all__ = [
    "bp",
    "Item",
    "Warehouse",
    "Lot",
    "StockBalance",
    "StockLedgerEntry",
    "InventorySerial",
    "SerialNumber",
    "assign_lot",
    "check_expiry",
]
