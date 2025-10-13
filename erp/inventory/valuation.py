# NOTE: This file is part of the ERP backbone patch.
# It assumes you have a Flask app factory and a SQLAlchemy `db` instance at `erp.extensions`.
# If your project uses a different path (e.g., `from extensions import db`), adjust the import below.
from datetime import datetime, date
from typing import Optional, List, Dict
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from sqlalchemy import func, Enum
try:
    from erp.extensions import db
except ImportError:  # fallback if project uses a flat `extensions.py`
    from extensions import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

from decimal import Decimal

def wac_rate(item_id, warehouse_id):
    """Compute Weighted Average Cost for item in a warehouse."""
    from erp.inventory.models import StockLedgerEntry  # local import to avoid circular
    ins = db.session.query(StockLedgerEntry).filter_by(item_id=item_id, warehouse_id=warehouse_id).order_by(StockLedgerEntry.posting_time.asc()).all()
    qty = Decimal("0")
    value = Decimal("0")
    for s in ins:
        qty += Decimal(str(s.qty))
        value += Decimal(str(s.value))
    if qty == 0:
        return Decimal("0")
    return (value / qty).quantize(Decimal("0.0001"))

def post_sle(item_id, warehouse_id, qty, voucher_type, voucher_id, lot_id=None, rate=None):
    from erp.inventory.models import StockLedgerEntry
    from decimal import Decimal
    if rate is None or rate == 0:
        rate = wac_rate(item_id, warehouse_id)
    value = (Decimal(str(qty)) * Decimal(str(rate))).quantize(Decimal("0.01"))
    sle = StockLedgerEntry(item_id=item_id, warehouse_id=warehouse_id, lot_id=lot_id, qty=qty, rate=rate, value=value, voucher_type=voucher_type, voucher_id=voucher_id)
    db.session.add(sle)
    db.session.commit()
    return sle.id
