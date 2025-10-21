from __future__ import annotations
from datetime import datetime, date
from erp.models import db

class Recruitment(db.Model):
    __tablename__ = "recruitments"

    id = db.Column(db.Integer, primary_key=True)

    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    position = db.Column(db.String(255), nullable=False)
    candidate_name  = db.Column(db.String(255), nullable=True)
    candidate_email = db.Column(db.String(255), nullable=True)

    status = db.Column(db.String(32), nullable=False, default="open")  # open|interviewing|hired|closed
    opened_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = db.relationship(
        "Organization",
        backref=db.backref("recruitments", lazy=True, cascade="all, delete-orphan"),
        foreign_keys=[organization_id],
    )

    @property
    def is_open(self) -> bool:
        return self.status in {"open", "interviewing"}

    def close(self, as_status: str = "closed") -> None:
        self.status = as_status
        self.closed_at = datetime.utcnow()

    def mark_hired(self) -> None:
        self.close(as_status="hired")

    def __repr__(self) -> str:
        return f"<Recruitment {self.id} {self.position!r} {self.status}>"



