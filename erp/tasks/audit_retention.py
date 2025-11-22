"""Retention sweeps for append-only audit logs."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from celery import shared_task

from erp.extensions import db
from erp.models import AuditLog


@shared_task(name="erp.tasks.audit.retention_sweep")
def retention_sweep(days_to_keep: int = 3650, hard_delete: bool = False):
    """Count (or optionally purge) audit logs older than *days_to_keep* days.

    By default this is non-destructive so compliance teams can archive logs to
    cold storage before removal. Set ``hard_delete=True`` only for non-regulated
    datasets or in sandbox environments.
    """

    cutoff = datetime.now(UTC) - timedelta(days=days_to_keep)

    old_q = AuditLog.query.filter(AuditLog.created_at < cutoff)
    count = old_q.count()

    if hard_delete:
        old_q.delete(synchronize_session=False)
        db.session.commit()

    return {"old_count": count, "hard_deleted": bool(hard_delete)}
