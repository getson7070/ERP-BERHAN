"""Module: models/performance_review.py — audit-added docstring. Refine with precise purpose when convenient."""
from __future__ import annotations
from datetime import date, datetime

from erp.models import db

class PerformanceReview(db.Model):
    __tablename__ = "performance_reviews"

    id = db.Column(db.Integer, primary_key=True)

    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    employee_name = db.Column(db.String(255), nullable=True)
    review_date = db.Column(db.Date, nullable=False, default=date.today)
    period_start = db.Column(db.Date, nullable=True)
    period_end = db.Column(db.Date, nullable=True)

    score = db.Column(db.Float, nullable=False, default=0.0)  # 0..5 (typical)
    comments = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(20), nullable=False, default="pending")  # pending|final
    completed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship(
        "User",
        backref=db.backref("reviews", lazy=True, cascade="all, delete-orphan"),
        foreign_keys=[user_id],
    )

    @classmethod
    def tenant_query(cls, org_id: int | None = None):
        query = cls.query
        if org_id is not None:
            query = query.filter_by(organization_id=org_id)
        return query

    @property
    def is_active_period(self) -> bool:
        today = date.today()
        return self.period_start <= today <= self.period_end

    def finalize(self) -> None:
        self.status = "final"
        self.completed_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<PerformanceReview {self.id} user={self.user_id} score={self.score}>"




