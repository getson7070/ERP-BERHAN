"""Scheduled data retention and anonymization tasks."""

from __future__ import annotations

import hashlib
from datetime import datetime, UTC

from erp import celery
from erp.utils import task_idempotent
from db import get_db


@celery.task(name="data_retention.purge_expired_rows")
@task_idempotent
def purge_expired_rows(idempotency_key: str | None = None) -> int:
    """Delete rows past their retention window."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM audit_logs WHERE delete_after IS NOT NULL AND delete_after < ?",
        (datetime.now(UTC),),
    )
    purged_logs = cur.rowcount
    cur.execute(
        "DELETE FROM invoices WHERE delete_after IS NOT NULL AND delete_after < ?",
        (datetime.now(UTC),),
    )
    purged_invoices = cur.rowcount
    conn.commit()
    conn.close()
    return purged_logs + purged_invoices


@celery.task(name="data_retention.anonymize_users")
@task_idempotent
def anonymize_users(idempotency_key: str | None = None) -> int:
    """Hash email addresses for inactive users marked for anonymization."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, email FROM users WHERE active = 0 AND anonymized = 0")
    rows = cur.fetchall()
    for user_id, email in rows:
        digest = hashlib.sha256(email.encode()).hexdigest()
        cur.execute(
            "UPDATE users SET email = ?, anonymized = 1 WHERE id = ?",
            (digest, user_id),
        )
    conn.commit()
    conn.close()
    return len(rows)


@celery.task(name="data_retention.run_access_recert_export")
@task_idempotent
def run_access_recert_export(idempotency_key: str | None = None) -> str:
    """Generate and persist an immutable access recertification export."""
    from scripts.access_recert_export import export

    output = export()
    return str(output)
