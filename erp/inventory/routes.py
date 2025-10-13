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
from .valuation import post_sle, wac_rate

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/items', methods=['GET','POST'])
@login_required
def items():
    if request.method == 'POST':
        data = request.json or {}
        obj = Item(code=data['code'], name=data['name'], uom=data.get('uom','Unit'))
        db.session.add(obj); db.session.commit()
        return jsonify(dict(id=str(obj.id))), 201
    rows = Item.query.order_by(Item.code).all()
    return jsonify([dict(id=str(r.id), code=r.code, name=r.name, uom=r.uom) for r in rows])

@inventory_bp.route('/warehouses', methods=['GET','POST'])
@login_required
def warehouses():
    if request.method == 'POST':
        data = request.json or {}
        obj = Warehouse(name=data['name'])
        db.session.add(obj); db.session.commit()
        return jsonify(dict(id=str(obj.id))), 201
    rows = Warehouse.query.order_by(Warehouse.name).all()
    return jsonify([dict(id=str(r.id), name=r.name) for r in rows])

@inventory_bp.route('/grn', methods=['POST'])
@login_required
def create_grn():
    data = request.json or {}
    grn = GRN(supplier_id=data.get('supplier_id'))
    db.session.add(grn); db.session.flush()
    # lines
    for ln in data.get('lines', []):
        post_sle(item_id=ln['item_id'], warehouse_id=ln['warehouse_id'], qty=Decimal(str(ln['qty'])), voucher_type='GRN', voucher_id=grn.id, lot_id=ln.get('lot_id'), rate=Decimal(str(ln.get('rate',0))))
    db.session.commit()
    return jsonify(dict(id=str(grn.id))), 201

@inventory_bp.route('/delivery', methods=['POST'])
@login_required
def create_delivery():
    data = request.json or {}
    d = Delivery(customer_id=data.get('customer_id'))
    db.session.add(d); db.session.flush()
    for ln in data.get('lines', []):
        post_sle(item_id=ln['item_id'], warehouse_id=ln['warehouse_id'], qty=Decimal(str(-abs(ln['qty']))), voucher_type='Delivery', voucher_id=d.id, lot_id=ln.get('lot_id'))
    db.session.commit()
    return jsonify(dict(id=str(d.id))), 201

@inventory_bp.route('/onhand/<item_id>/<warehouse_id>', methods=['GET'])
@login_required
def onhand(item_id, warehouse_id):
    from .models import StockLedgerEntry
    q = db.session.query(func.coalesce(func.sum(StockLedgerEntry.qty), 0)).filter_by(item_id=item_id, warehouse_id=warehouse_id).scalar()
    rate = wac_rate(item_id, warehouse_id)
    return jsonify(dict(item_id=item_id, warehouse_id=warehouse_id, qty=float(q or 0), wac=float(rate)))
