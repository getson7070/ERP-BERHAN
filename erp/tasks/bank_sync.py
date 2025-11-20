"""Celery task for fetching bank statements via external APIs."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from celery import shared_task

from erp.extensions import db
from erp.models import (
    BankAccessToken,
    BankAccount,
    BankConnection,
    BankStatement,
    BankStatementLine,
    BankSyncJob,
    FinanceAuditLog,
)


def _get_latest_token(org_id: int, connection_id: int) -> BankAccessToken | None:
    return (
        BankAccessToken.query.filter_by(org_id=org_id, connection_id=connection_id)
        .order_by(BankAccessToken.created_at.desc())
        .first()
    )


def _fetch_statements_from_api(
    conn: BankConnection,
    token: BankAccessToken,
    bank_account: BankAccount,
    date_from,
    date_to,
) -> list[dict]:
    """Provider-agnostic placeholder returning normalized statement rows."""

    # In production, route to provider-specific adapters using conn.provider
    # and conn.api_base_url. For now, return an empty list to keep the task
    # deterministic in tests.
    return []


@shared_task(name="erp.tasks.bank_sync.run_sync_job")
def run_sync_job(job_id: int):
    job = BankSyncJob.query.get(job_id)
    if not job or job.status not in ("pending", "error"):
        return

    job.status = "running"
    job.started_at = datetime.utcnow()
    db.session.commit()

    try:
        conn: BankConnection = job.connection
        bank_account: BankAccount = job.bank_account
        token = _get_latest_token(job.org_id, conn.id)
        if not token:
            raise RuntimeError("No access token configured for this connection")

        rows = _fetch_statements_from_api(
            conn,
            token,
            bank_account,
            job.requested_from,
            job.requested_to,
        )

        stmt = BankStatement(
            org_id=job.org_id,
            bank_account_id=bank_account.id,
            bank_account_code=bank_account.gl_account_code or (bank_account.account_number or ""),
            currency=bank_account.currency,
            period_start=job.requested_from,
            period_end=job.requested_to,
            opening_balance=Decimal("0"),
            closing_balance=Decimal("0"),
            source="API",
            external_reference=f"conn:{conn.id}:job:{job.id}",
            created_by_id=job.requested_by_id,
        )
        db.session.add(stmt)
        db.session.flush()

        lines_created = 0
        for raw in rows:
            line = BankStatementLine(
                org_id=job.org_id,
                statement_id=stmt.id,
                tx_date=raw["tx_date"],
                description=raw.get("description"),
                amount=Decimal(str(raw["amount"])),
                balance=Decimal(str(raw.get("balance", "0"))),
            )
            db.session.add(line)
            lines_created += 1

        job.status = "success"
        job.finished_at = datetime.utcnow()
        job.statements_created = 1
        job.lines_created = lines_created

        db.session.add(
            FinanceAuditLog(
                org_id=job.org_id,
                event_type="BANK_SYNC_JOB_SUCCESS",
                entity_type="BANK_SYNC_JOB",
                entity_id=job.id,
                payload={
                    "connection": conn.name,
                    "bank_account": bank_account.name,
                    "lines_created": lines_created,
                },
                created_by_id=job.requested_by_id,
            )
        )

        db.session.commit()
    except Exception as exc:  # pragma: no cover - defensive logging
        job.status = "error"
        job.finished_at = datetime.utcnow()
        job.error_message = str(exc)

        db.session.add(
            FinanceAuditLog(
                org_id=job.org_id,
                event_type="BANK_SYNC_JOB_ERROR",
                entity_type="BANK_SYNC_JOB",
                entity_id=job.id,
                payload={"error": str(exc)},
                created_by_id=job.requested_by_id,
            )
        )
        db.session.commit()
