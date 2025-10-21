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

class PurchaseOrder(db.Model):
    __tablename__ = "purchase_orders"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = db.Column(UUID(as_uuid=True))
    posting_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(16), default="Draft")  # Draft, Submitted, Ordered, Received, Closed


