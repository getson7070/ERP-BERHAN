"""Durable audit logging helpers backed by SQLAlchemy."""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Iterable, Optional

from sqlalchemy import select

from erp.extensions import db
from erp.models import AuditLog
from erp.services.audit_log_service import write_audit_log
from .metrics import AUDIT_CHAIN_BROKEN


def _hash_entry(prev_hash, user_id, org_id, action, details, created_at):
    prev = prev_hash or ""
    det = details or ""
    s = f"{prev}|{user_id}|{org_id}|{action}|{det}|{created_at}"
    return hashlib.sha256(s.encode()).hexdigest()


def log_audit(
    user_id: int | None,
    org_id: int | None,
    action: str,
    details: Optional[str] = None,
    metadata: Optional[dict] = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
) -> AuditLog:
    """Persist an audit log entry inside the primary database.

    Compatibility wrapper: preserves the legacy hash-chain while emitting the
    richer audit envelope used by the new audit API. The metadata dictionary is
    merged with a "details" key so consumers can search on the free-form text.
    """

    session = db.session
    prev_hash = session.execute(
        select(AuditLog.hash).order_by(AuditLog.id.desc()).limit(1)
    ).scalar()
    created_at = datetime.now(UTC)
    entry_hash = _hash_entry(prev_hash, user_id, org_id, action, details, created_at.isoformat())

    base_metadata = dict(metadata or {})
    if details:
        base_metadata.setdefault("details", details)

    audit_row = write_audit_log(
        org_id=org_id or 0,
        module=action.split(".")[0] if "." in action else "general",
        action=action,
        actor_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=base_metadata,
    )

    audit_row.prev_hash = prev_hash
    audit_row.hash = entry_hash
    audit_row.details = details
    audit_row.created_at = created_at
    session.commit()
    return audit_row


def check_audit_chain(records: Optional[Iterable[AuditLog]] = None) -> int:
    """Validate the tamper-evident hash chain."""

    close_session = False
    if records is None:
        close_session = True
        records = db.session.execute(
            select(AuditLog).order_by(AuditLog.id)
        ).scalars().all()

    breaks = 0
    prev_hash = None
    for row in records:
        calc = _hash_entry(
            prev_hash,
            row.user_id,
            row.org_id,
            row.action,
            row.details,
            row.created_at.isoformat(),
        )
        if calc != row.hash:
            breaks += 1
        prev_hash = row.hash

    if breaks:
        AUDIT_CHAIN_BROKEN.inc(breaks)

    if close_session:
        db.session.remove()

    return breaks
