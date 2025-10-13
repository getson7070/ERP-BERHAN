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

class Account(db.Model):
    __tablename__ = "accounts"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company = db.Column(db.String(128), nullable=False, default="DefaultCo")
    code = db.Column(db.String(32), nullable=False, unique=True)
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(32), nullable=False)  # ASSET, LIABILITY, EQUITY, INCOME, EXPENSE
    is_group = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return dict(id=str(self.id), company=self.company, code=self.code, name=self.name, type=self.type, is_group=self.is_group)

class JournalEntry(db.Model):
    __tablename__ = "journal_entries"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    posting_date = db.Column(db.Date, nullable=False, default=date.today)
    reference = db.Column(db.String(128))
    remarks = db.Column(db.Text)
    submitted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lines = relationship("JournalLine", back_populates="entry", cascade="all, delete-orphan")

    def post(self):
        self.submitted = True

    def to_dict(self, with_lines=True):
        base = dict(id=str(self.id), posting_date=self.posting_date.isoformat(), reference=self.reference, remarks=self.remarks, submitted=self.submitted)
        if with_lines:
            base["lines"] = [l.to_dict() for l in self.lines]
        return base

class JournalLine(db.Model):
    __tablename__ = "journal_lines"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = db.Column(UUID(as_uuid=True), db.ForeignKey("journal_entries.id"), nullable=False, index=True)
    account_id = db.Column(UUID(as_uuid=True), db.ForeignKey("accounts.id"), nullable=False)
    party_type = db.Column(db.String(16))  # Customer, Supplier
    party_id = db.Column(UUID(as_uuid=True))
    debit = db.Column(db.Numeric(18,2), default=0)
    credit = db.Column(db.Numeric(18,2), default=0)
    description = db.Column(db.String(255))

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")

    def to_dict(self):
        return dict(id=str(self.id), entry_id=str(self.entry_id), account_id=str(self.account_id), debit=float(self.debit or 0), credit=float(self.credit or 0), description=self.description)

class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(128), nullable=False, unique=True)
    currency = db.Column(db.String(8), default="ETB")

class Supplier(db.Model):
    __tablename__ = "suppliers"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(128), nullable=False, unique=True)
    currency = db.Column(db.String(8), default="ETB")

class Invoice(db.Model):
    __tablename__ = "invoices"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey("customers.id"))
    posting_date = db.Column(db.Date, default=date.today)
    total = db.Column(db.Numeric(18,2), nullable=False)
    status = db.Column(db.String(16), default="Draft")  # Draft, Submitted, Paid, Cancelled

class Receipt(db.Model):
    __tablename__ = "receipts"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = db.Column(UUID(as_uuid=True), db.ForeignKey("invoices.id"))
    amount = db.Column(db.Numeric(18,2), nullable=False)
    received_on = db.Column(db.Date, default=date.today)

class Bill(db.Model):
    __tablename__ = "bills"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = db.Column(UUID(as_uuid=True), db.ForeignKey("suppliers.id"))
    posting_date = db.Column(db.Date, default=date.today)
    total = db.Column(db.Numeric(18,2), nullable=False)
    status = db.Column(db.String(16), default="Draft")  # Draft, Submitted, Paid, Cancelled

class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = db.Column(UUID(as_uuid=True), db.ForeignKey("bills.id"))
    amount = db.Column(db.Numeric(18,2), nullable=False)
    paid_on = db.Column(db.Date, default=date.today)
