from .models import Account, JournalEntry, JournalLine, Invoice, Bill
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

finance_bp = Blueprint('finance', __name__, url_prefix='/finance')

@finance_bp.route('/accounts', methods=['GET','POST'])
@login_required
def accounts():
    if request.method == 'POST':
        data = request.json or {}
        acc = Account(code=data['code'], name=data['name'], type=data.get('type','ASSET'), company=data.get('company','DefaultCo'))
        db.session.add(acc); db.session.commit()
        return jsonify(acc.to_dict()), 201
    # GET
    rows = Account.query.order_by(Account.code).all()
    return jsonify([r.to_dict() for r in rows])

@finance_bp.route('/journals', methods=['GET','POST'])
@login_required
def journals():
    if request.method == 'POST':
        data = request.json or {}
        je = JournalEntry(posting_date=date.fromisoformat(data.get('posting_date', date.today().isoformat())), reference=data.get('reference'), remarks=data.get('remarks'))
        for ln in data.get('lines', []):
            line = JournalLine(account_id=ln['account_id'], debit=ln.get('debit',0), credit=ln.get('credit',0), description=ln.get('description'))
            je.lines.append(line)
        db.session.add(je); db.session.commit()
        return jsonify(je.to_dict()), 201
    # GET
    rows = JournalEntry.query.order_by(JournalEntry.posting_date.desc(), JournalEntry.created_at.desc()).limit(200).all()
    return jsonify([r.to_dict() for r in rows])

@finance_bp.route('/ar/invoices', methods=['GET','POST'])
@login_required
def ar_invoices():
    if request.method == 'POST':
        data = request.json or {}
        inv = Invoice(customer_id=data['customer_id'], total=data['total'])
        db.session.add(inv); db.session.commit()
        return jsonify(dict(id=str(inv.id))), 201
    rows = Invoice.query.order_by(Invoice.posting_date.desc()).limit(200).all()
    return jsonify([dict(id=str(r.id), total=float(r.total), status=r.status, posting_date=r.posting_date.isoformat()) for r in rows])

@finance_bp.route('/ap/bills', methods=['GET','POST'])
@login_required
def ap_bills():
    if request.method == 'POST':
        data = request.json or {}
        b = Bill(supplier_id=data['supplier_id'], total=data['total'])
        db.session.add(b); db.session.commit()
        return jsonify(dict(id=str(b.id))), 201
    rows = Bill.query.order_by(Bill.posting_date.desc()).limit(200).all()
    return jsonify([dict(id=str(r.id), total=float(r.total), status=r.status, posting_date=r.posting_date.isoformat()) for r in rows])

