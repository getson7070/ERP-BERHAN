"""Durable audit log persisted in the primary database."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Index

from . import db


class AuditLog(db.Model):
    """Tamper-evident audit log row."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_org_action", "org_id", "action"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    org_id = db.Column(db.Integer, db.ForeignKey("organizations.id", ondelete="SET NULL"))
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    prev_hash = db.Column(db.String(128), nullable=True)
    hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditLog id={self.id} action={self.action!r}>"
