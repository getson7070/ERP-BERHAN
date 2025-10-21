from datetime import datetime
from erp.extensions import db

class Invoice(db.Model):
    __tablename__ = "invoices"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    customer = db.Column(db.String(255), nullable=False)
    currency = db.Column(db.String(8), nullable=False, default="ETB")
    total = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    status = db.Column(db.String(32), nullable=False, default="draft")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    method = db.Column(db.String(32), nullable=False, default="cash")
    received_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    invoice = db.relationship("Invoice", backref=db.backref("payments", lazy="dynamic"))



