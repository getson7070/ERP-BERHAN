# erp/inventory/models.py â€” clean models (items, warehouses, lots, ledger)
from __future__ import annotations
from datetime import datetime, date
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..extensions import db

class Warehouse(db.Model):
    __tablename__ = "warehouses"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(128), unique=True, nullable=False)

class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = db.Column(db.String(64), unique=True, nullable=False)   # keep template compatibility
    name = db.Column(db.String(255), nullable=False)
    uom = db.Column(db.String(32), default="Unit")

class Lot(db.Model):
    __tablename__ = "lots"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("items.id"), nullable=False, index=True)
    number = db.Column(db.String(64), index=True)
    expiry = db.Column(db.Date)

class StockLedgerEntry(db.Model):
    __tablename__ = "stock_ledger_entries"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    posting_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("items.id"), nullable=False, index=True)
    warehouse_id = db.Column(UUID(as_uuid=True), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    lot_id = db.Column(UUID(as_uuid=True), db.ForeignKey("lots.id"), nullable=True, index=True)
    qty = db.Column(db.Numeric(18,3), nullable=False)  # +in / -out
    rate = db.Column(db.Numeric(18,4), nullable=False, default=0) # unit cost (WAC placeholder)
    value = db.Column(db.Numeric(18,2), nullable=False, default=0) # qty*rate
    voucher_type = db.Column(db.String(32))
    voucher_id = db.Column(UUID(as_uuid=True))


