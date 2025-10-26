from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from erp.extensions import db
from erp.models.finance import Invoice, Payment

finance_bp = Blueprint("finance", __name__, url_prefix="/finance")

@finance_bp.get("/health")
def health():
    return jsonify(ok=True, module="finance")

@finance_bp.get("/invoices")
def list_invoices():
    q = Invoice.query.order_by(Invoice.created_at.desc()).limit(50).all()
    return jsonify([{
        "id": i.id, "number": i.number, "customer": i.customer, "currency": i.currency,
        "total": str(i.total), "status": i.status, "created_at": i.created_at.isoformat()
    } for i in q])

@finance_bp.post("/invoices")
def create_invoice():
    data = request.get_json() or {}
    if not data.get("number"):
        return jsonify(error="number_required"), 400
    inv = Invoice(
        number=data["number"],
        customer=data.get("customer", "UNKNOWN"),
        currency=data.get("currency", "ETB"),
        total=Decimal(str(data.get("total", "0"))),
        status=data.get("status", "draft"),
    )
    db.session.add(inv)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify(error="invoice_exists", detail=str(e)), 400
    return jsonify(id=inv.id, number=inv.number), 201

@finance_bp.post("/payments")
def add_payment():
    data = request.get_json() or {}
    if not data.get("invoice_id"):
        return jsonify(error="invoice_id_required"), 400
    pay = Payment(
        invoice_id=int(data["invoice_id"]),
        amount=Decimal(str(data.get("amount", "0"))),
        method=data.get("method", "cash"),
    )
    db.session.add(pay)
    db.session.commit()
    return jsonify(id=pay.id), 201

# alias for dynamic importer
bp = finance_bp

