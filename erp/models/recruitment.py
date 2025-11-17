"""Module: models/recruitment.py — audit-added docstring. Refine with precise purpose when convenient."""
from __future__ import annotations
from datetime import UTC, datetime

from erp.models import db

class Recruitment(db.Model):
    __tablename__ = "recruitments"

    id = db.Column(db.Integer, primary_key=True)

    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    position = db.Column(db.String(255), nullable=False)
    candidate_name = db.Column(db.String(255), nullable=True)
    candidate_email = db.Column(db.String(255), nullable=True)
    candidate_phone = db.Column(db.String(50), nullable=True)
    source = db.Column(db.String(64), nullable=True)  # referral|job_board|career_fair|internal
    resume_url = db.Column(db.String(512), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(32), nullable=False, default="open")  # open|interviewing|hired|closed
    stage = db.Column(db.String(32), nullable=False, default="screening")  # screening|panel|offer
    recruiter_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    applied_on = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    opened_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    closed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    organization = db.relationship(
        "Organization",
        backref=db.backref("recruitments", lazy=True, cascade="all, delete-orphan"),
        foreign_keys=[organization_id],
    )

    @classmethod
    def tenant_query(cls, org_id: int | None = None):
        query = cls.query
        if org_id is not None:
            query = query.filter_by(organization_id=org_id)
        return query

    @property
    def is_open(self) -> bool:
        return self.status in {"open", "interviewing"}

    def close(self, as_status: str = "closed") -> None:
        self.status = as_status
        self.closed_at = datetime.now(UTC)

    def mark_hired(self) -> None:
        self.close(as_status="hired")

    def __repr__(self) -> str:
        return f"<Recruitment {self.id} {self.position!r} {self.status}>"




