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

from sqlalchemy.orm import relationship

class Warehouse(db.Model):
    __tablename__ = "warehouses"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(128), unique=True, nullable=False)

class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    uom = db.Column(db.String(32), default="Unit")
    valuation_method = db.Column(db.String(8), default="WAC")  # WAC only initially

class Lot(db.Model):
    __tablename__ = "lots"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("items.id"), index=True, nullable=False)
    number = db.Column(db.String(64), index=True)
    expiry = db.Column(db.Date)

class StockLedgerEntry(db.Model):
    __tablename__ = "stock_ledger_entries"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    posting_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("items.id"), index=True, nullable=False)
    warehouse_id = db.Column(UUID(as_uuid=True), db.ForeignKey("warehouses.id"), index=True, nullable=False)
    lot_id = db.Column(UUID(as_uuid=True), db.ForeignKey("lots.id"), index=True, nullable=True)
    qty = db.Column(db.Numeric(18,3), nullable=False)  # +in / -out
    rate = db.Column(db.Numeric(18,4), nullable=False) # unit value at time of posting (WAC)
    value = db.Column(db.Numeric(18,2), nullable=False) # qty * rate
    voucher_type = db.Column(db.String(32))  # GRN, Delivery, Transfer
    voucher_id = db.Column(UUID(as_uuid=True))

class GRN(db.Model):
    __tablename__ = "grn"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = db.Column(UUID(as_uuid=True))
    posting_date = db.Column(db.Date, default=date.today)

class Delivery(db.Model):
    __tablename__ = "deliveries"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = db.Column(UUID(as_uuid=True))
    posting_date = db.Column(db.Date, default=date.today)
