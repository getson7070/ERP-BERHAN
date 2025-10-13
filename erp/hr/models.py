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

class Recruitment(db.Model):
    __tablename__ = "recruitment"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position = db.Column(db.String(128), nullable=False)
    candidate = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(32), default="Applied")  # Applied, Interview, Offer, Hired, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PerformanceReview(db.Model):
    __tablename__ = "performance_reviews"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = db.Column(UUID(as_uuid=True))
    period = db.Column(db.String(32), nullable=False)  # e.g., 2025-Q1
    score = db.Column(db.Numeric(5,2), default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
