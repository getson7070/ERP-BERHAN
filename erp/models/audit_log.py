"""Durable audit log persisted in the primary database."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Index

from . import db


class AuditLog(db.Model):
    """Tamper-evident audit log row.

    The table is append-only and captures a searchable metadata envelope
    alongside an encrypted payload for sensitive fields. Existing hash-chain
    fields are preserved for compatibility with prior integrity checks.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_org_action", "org_id", "action"),
        Index("ix_audit_org_mod_action_time", "org_id", "module", "action", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    org_id = db.Column(db.Integer, db.ForeignKey("organizations.id", ondelete="SET NULL"))

    actor_type = db.Column(db.String(32), nullable=False, server_default="user", index=True)
    actor_id = db.Column(db.Integer, nullable=True, index=True)

    ip_address = db.Column(db.String(64), nullable=True, index=True)
    user_agent = db.Column(db.String(255), nullable=True)
    request_id = db.Column(db.String(64), nullable=True, index=True)

    module = db.Column(db.String(64), nullable=False, server_default="general", index=True)
    action = db.Column(db.String(255), nullable=False, index=True)
    severity = db.Column(db.String(16), nullable=False, server_default="info", index=True)

    entity_type = db.Column(db.String(64), nullable=True, index=True)
    entity_id = db.Column(db.Integer, nullable=True, index=True)

    metadata_json = db.Column(db.JSON, nullable=False, default=dict, server_default=db.text("'{}'"))
    payload_encrypted = db.Column(db.JSON, nullable=True)

    # Legacy hash-chain fields retained for tamper-evidence compatibility
    details = db.Column(db.Text, nullable=True)
    prev_hash = db.Column(db.String(128), nullable=True)
    hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditLog id={self.id} action={self.action!r}>"
