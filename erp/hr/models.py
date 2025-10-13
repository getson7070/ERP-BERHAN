from __future__ import annotations
from datetime import datetime
from ..extensions import db

class Recruitment(db.Model):
    __tablename__ = "recruitment"
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.String(128), nullable=False)
    candidate = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(32), default="Applied", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class PerformanceReview(db.Model):
    __tablename__ = "performance_reviews"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, nullable=True)
    period = db.Column(db.String(32), nullable=False)  # e.g., 2025-Q4
    score = db.Column(db.Numeric(5,2), default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
