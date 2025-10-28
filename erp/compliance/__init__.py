"""Compliance models for Part 11/GMP workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256

from ..extensions import db
from .privacy import (
    AssessmentSummary,
    PolicyLink,
    PrivacyFrameworkStatus,
    PrivacyImpactAssessment,
    PrivacyProgramSnapshot,
    UpcomingReview,
    build_privacy_program_snapshot,
)


class ElectronicSignature(db.Model):  # type: ignore[name-defined]
    """Store electronic signatures with tamper-evident hash chain."""

    __tablename__ = "electronic_signatures"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    intent = db.Column(db.String(255), nullable=False)
    signed_at = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
    prev_hash = db.Column(db.String(64))
    signature_hash = db.Column(db.String(64), nullable=False)

    def __init__(self, **kwargs):
        if "signed_at" not in kwargs:
            kwargs["signed_at"] = datetime.now(UTC)
        super().__init__(**kwargs)
        self._apply_hash()

    def _apply_hash(self) -> None:
        """Compute chained hash for tamper evidence."""
        prev = ElectronicSignature.query.order_by(ElectronicSignature.id.desc()).first()
        prev_hash = prev.signature_hash if prev else ""
        payload = f"{self.user_id}{self.intent}{self.signed_at.isoformat()}{prev_hash}".encode()
        self.prev_hash = prev_hash or None
        self.signature_hash = sha256(payload).hexdigest()


class BatchRecord(db.Model):  # type: ignore[name-defined]
    """Electronic batch record for manufacturing lots."""

    __tablename__ = "batch_records"

    id = db.Column(db.Integer, primary_key=True)
    lot_number = db.Column(db.String(64), nullable=False, unique=True, index=True)
    description = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class NonConformance(db.Model):  # type: ignore[name-defined]
    """Track deviations from standard processes."""

    __tablename__ = "non_conformances"

    id = db.Column(db.Integer, primary_key=True)
    batch_record_id = db.Column(
        db.Integer, db.ForeignKey("batch_records.id"), nullable=False
    )
    description = db.Column(db.Text, nullable=False)
    detected_at = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
    resolved_at = db.Column(db.DateTime)
    status = db.Column(db.String(32), default="open", nullable=False)

    batch_record = db.relationship("BatchRecord", backref="non_conformances")


__all__ = [
    "ElectronicSignature",
    "BatchRecord",
    "NonConformance",
    "AssessmentSummary",
    "PolicyLink",
    "PrivacyFrameworkStatus",
    "PrivacyImpactAssessment",
    "PrivacyProgramSnapshot",
    "UpcomingReview",
    "build_privacy_program_snapshot",
]


