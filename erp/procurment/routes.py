from .models import PurchaseOrder
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

proc_bp = Blueprint('procurement', __name__, url_prefix='/procurement')

@proc_bp.route('/po', methods=['GET','POST'])
@login_required
def purchase_orders():
    if request.method == 'POST':
        data = request.json or {}
        po = PurchaseOrder(supplier_id=data.get('supplier_id'))
        db.session.add(po); db.session.commit()
        return jsonify(dict(id=str(po.id))), 201
    rows = PurchaseOrder.query.order_by(PurchaseOrder.posting_date.desc()).limit(200).all()
    return jsonify([dict(id=str(r.id), status=r.status, posting_date=r.posting_date.isoformat()) for r in rows])

