"""Module: models/performance_review.py — audit-added docstring. Refine with precise purpose when convenient."""
from __future__ import annotations
from datetime import UTC, date, datetime

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

    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    goals = db.Column(db.Text, nullable=True)
    competencies = db.Column(db.Text, nullable=True)

    score = db.Column(db.Float, nullable=False, default=0.0)  # 0..5 (typical)
    comments = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(20), nullable=False, default="pending")  # pending|final
    completed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

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
        if self.period_start and self.period_end:
            return self.period_start <= today <= self.period_end
        return False

    def finalize(self) -> None:
        self.status = "final"
        self.completed_at = datetime.now(UTC)

    def __repr__(self) -> str:
        return f"<PerformanceReview {self.id} user={self.user_id} score={self.score}>"




