"""Retention and anonymization tasks.

Scheduled Celery jobs to purge expired data, anonymize PII and export
quarterly access recertification reports.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, UTC
from sqlalchemy import text

# ---- Optional Celery imports (safe when Celery isn't installed) ---------------
try:
    from celery.schedules import crontab  # type: ignore
except Exception:  # pragma: no cover
    def crontab(*_args, **_kwargs):
        return None  # stub so tests can import this module without Celery

try:
    # Reuse analytics Celery app if available
    from erp.routes.analytics import celery as _celery  # type: ignore
except Exception:  # pragma: no cover
    # Minimal shim so @celery.task is a no-op in tests
    class _DummySignal:
        def connect(self, f):  # type: ignore[no-untyped-def]
            return f

    class _DummyCelery:
        on_after_finalize = _DummySignal()

        def task(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            def _decorator(fn):
                return fn
            return _decorator

    _celery = _DummyCelery()

celery = _celery  # public name

from erp.utils import task_idempotent
from db import get_db
from scripts.access_recert_export import export as export_recert
# -----------------------------------------------------------------------------

def _connect_signal_or_noop(app):
    try:
        return app.on_after_finalize.connect
    except Exception:
        def _noop(f):
            return f
        return _noop


@_connect_signal_or_noop(celery)  # <-- this decorator wires periodic tasks (no-op in tests)
def setup_periodic_tasks(sender, **kwargs):  # pragma: no cover - schedule wiring
    """Register periodic jobs."""
    sender.add_periodic_task(
        crontab(hour=3, minute=0),
        purge_expired_records.s(),
        name="purge-expired-records",
    )
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        anonymize_users.s(),
        name="anonymize-old-users",
    )
    sender.add_periodic_task(
        crontab(month_of_year="1,4,7,10", day_of_month=1, hour=5, minute=0),
        run_access_recert_export.s(),
        name="quarterly-access-recert-export",
    )


@celery.task(name="data_retention.purge_expired_records")
@task_idempotent
def purge_expired_records(idempotency_key: str | None = None) -> int:
    """Delete rows past their retention window."""
    now = datetime.now(UTC)
    conn = get_db()
    cur = conn.execute(
        text("DELETE FROM audit_logs WHERE retain_until < :now"),
        {"now": now},
    )
    purged_logs = cur.rowcount
    cur = conn.execute(
        text("DELETE FROM users WHERE retain_until < :now"),
        {"now": now},
    )
    purged_users = cur.rowcount
    conn.commit()
    conn.close()
    return (purged_logs or 0) + (purged_users or 0)


@celery.task(name="data_retention.anonymize_users")
@task_idempotent
def anonymize_users(idempotency_key: str | None = None) -> int:
    """Hash email addresses for inactive users marked for anonymization."""
    now = datetime.now(UTC)
    conn = get_db()
    rows = conn.execute(
        text(
            "SELECT id, email FROM users "
            "WHERE active = 0 AND anonymized = 0 AND retain_until < :now"
        ),
        {"now": now},
    ).fetchall()
    for user_id, email in rows:
        digest = hashlib.sha256(email.encode()).hexdigest()
        conn.execute(
            text("UPDATE users SET email = :email, anonymized = 1 WHERE id = :id"),
            {"email": digest, "id": user_id},
        )
    conn.commit()
    conn.close()
    return len(rows)


@celery.task(name="data_retention.run_access_recert_export")
@task_idempotent
def run_access_recert_export(idempotency_key: str | None = None) -> str:
    """Generate and persist an immutable access recertification export."""
    output = export_recert()
    return str(output)
