"""Banking integration endpoints: accounts, connections, tokens, sync jobs, cashflow."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from erp.celery_app import celery_app
from erp.extensions import db
from erp.models import (
    BankAccessToken,
    BankAccount,
    BankConnection,
    BankStatementLine,
    BankSyncJob,
    BankTwoFactorChallenge,
    FinanceAuditLog,
)
from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("banking_api", __name__, url_prefix="/api/banking")


# ---------------------------------------------------------------------------
# Bank accounts CRUD
# ---------------------------------------------------------------------------


def _serialize_bank_account(acc: BankAccount) -> dict[str, Any]:
    return {
        "id": acc.id,
        "name": acc.name,
        "bank_name": acc.bank_name,
        "account_number_masked": acc.account_number_masked,
        "currency": acc.currency,
        "gl_account_code": acc.gl_account_code,
        "is_default": acc.is_default,
        "is_active": acc.is_active,
        "created_at": acc.created_at.isoformat() if acc.created_at else None,
    }


@bp.get("/accounts")
@require_roles("finance", "admin")
def list_bank_accounts():
    org_id = resolve_org_id()
    q = BankAccount.query.filter_by(org_id=org_id, is_active=True).order_by(BankAccount.name.asc())
    return jsonify([_serialize_bank_account(a) for a in q.all()]), HTTPStatus.OK


@bp.post("/accounts")
@require_roles("finance", "admin")
def create_bank_account():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    name = (payload.get("name") or "").strip()
    bank_name = (payload.get("bank_name") or "").strip()
    account_number_masked = (payload.get("account_number_masked") or "").strip()
    gl_code = (payload.get("gl_account_code") or "").strip()

    if not (name and bank_name and account_number_masked and gl_code):
        return (
            jsonify({"error": "name, bank_name, account_number_masked, gl_account_code are required"}),
            HTTPStatus.BAD_REQUEST,
        )

    acc = BankAccount(
        org_id=org_id,
        name=name,
        bank_name=bank_name,
        account_number_masked=account_number_masked,
        currency=(payload.get("currency") or "ETB").upper(),
        gl_account_code=gl_code,
        is_default=bool(payload.get("is_default", False)),
        is_active=True,
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(acc)
    db.session.commit()
    return jsonify(_serialize_bank_account(acc)), HTTPStatus.CREATED


# ---------------------------------------------------------------------------
# Bank connections (API config)
# ---------------------------------------------------------------------------


def _serialize_connection(conn: BankConnection) -> dict[str, Any]:
    return {
        "id": conn.id,
        "name": conn.name,
        "provider": conn.provider,
        "environment": conn.environment,
        "api_base_url": conn.api_base_url,
        "requires_two_factor": conn.requires_two_factor,
        "two_factor_method": conn.two_factor_method,
        "last_connected_at": conn.last_connected_at.isoformat() if conn.last_connected_at else None,
    }


@bp.get("/connections")
@require_roles("finance", "admin")
def list_connections():
    org_id = resolve_org_id()
    q = BankConnection.query.filter_by(org_id=org_id).order_by(BankConnection.name.asc())
    return jsonify([_serialize_connection(c) for c in q.all()]), HTTPStatus.OK


@bp.post("/connections")
@require_roles("finance", "admin")
def create_connection():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    name = (payload.get("name") or "").strip()
    provider = (payload.get("provider") or "").strip().upper()
    environment = (payload.get("environment") or "sandbox").lower()

    if not (name and provider):
        return jsonify({"error": "name and provider are required"}), HTTPStatus.BAD_REQUEST

    conn = BankConnection(
        org_id=org_id,
        name=name,
        provider=provider,
        environment=environment,
        api_base_url=(payload.get("api_base_url") or "").strip() or None,
        credentials_json=payload.get("credentials") or {},
        requires_two_factor=bool(payload.get("requires_two_factor", False)),
        two_factor_method=(payload.get("two_factor_method") or "").strip() or None,
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(conn)
    db.session.commit()
    return jsonify(_serialize_connection(conn)), HTTPStatus.CREATED


@bp.post("/connections/<int:connection_id>/tokens")
@require_roles("finance", "admin")
def upsert_access_token(connection_id: int):
    """Store or update access/refresh tokens from OAuth / bank login flow."""

    org_id = resolve_org_id()
    conn = BankConnection.query.filter_by(org_id=org_id, id=connection_id).first_or_404()

    payload = request.get_json(silent=True) or {}
    access_token = (payload.get("access_token") or "").strip()
    if not access_token:
        return jsonify({"error": "access_token is required"}), HTTPStatus.BAD_REQUEST

    refresh_token = (payload.get("refresh_token") or "").strip() or None
    token_type = (payload.get("token_type") or "").strip() or None
    scope = (payload.get("scope") or "").strip() or None
    expires_at_raw = payload.get("expires_at")
    expires_at = datetime.fromisoformat(expires_at_raw) if expires_at_raw else None

    token = BankAccessToken(
        org_id=org_id,
        connection_id=conn.id,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=token_type,
        scope=scope,
        expires_at=expires_at,
        created_by_id=getattr(current_user, "id", None),
    )
    conn.last_connected_at = datetime.utcnow()
    db.session.add(token)
    db.session.add(
        FinanceAuditLog(
            org_id=org_id,
            event_type="BANK_TOKEN_UPSERTED",
            entity_type="BANK_CONNECTION",
            entity_id=conn.id,
            payload={"provider": conn.provider, "environment": conn.environment},
            created_by_id=getattr(current_user, "id", None),
        )
    )
    db.session.commit()
    return jsonify({"status": "ok"}), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Two-factor challenge (OTP-style)
# ---------------------------------------------------------------------------


@bp.post("/connections/<int:connection_id>/2fa/challenge")
@require_roles("finance", "admin")
def create_two_factor_challenge(connection_id: int):
    org_id = resolve_org_id()
    conn = BankConnection.query.filter_by(org_id=org_id, id=connection_id).first_or_404()

    payload = request.get_json(silent=True) or {}
    challenge_type = (payload.get("challenge_type") or "otp").lower()
    challenge_id = (payload.get("challenge_id") or "").strip() or None

    chal = BankTwoFactorChallenge(
        org_id=org_id,
        connection_id=conn.id,
        challenge_type=challenge_type,
        challenge_id=challenge_id,
        status="pending",
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(chal)
    db.session.commit()
    return jsonify({"challenge_id": chal.id}), HTTPStatus.CREATED


@bp.post("/connections/<int:connection_id>/2fa/verify")
@require_roles("finance", "admin")
def verify_two_factor(connection_id: int):
    org_id = resolve_org_id()
    conn = BankConnection.query.filter_by(org_id=org_id, id=connection_id).first_or_404()

    payload = request.get_json(silent=True) or {}
    challenge_id = payload.get("challenge_id")
    success = bool(payload.get("success", True))

    if not challenge_id:
        return jsonify({"error": "challenge_id is required"}), HTTPStatus.BAD_REQUEST

    chal = BankTwoFactorChallenge.query.filter_by(
        org_id=org_id, connection_id=conn.id, id=challenge_id
    ).first_or_404()

    if chal.status != "pending":
        return jsonify({"error": f"challenge already {chal.status}"}), HTTPStatus.BAD_REQUEST

    chal.status = "success" if success else "failed"
    chal.resolved_at = datetime.utcnow()
    chal.resolved_by_id = getattr(current_user, "id", None)

    db.session.add(
        FinanceAuditLog(
            org_id=org_id,
            event_type="BANK_2FA_VERIFIED",
            entity_type="BANK_CONNECTION",
            entity_id=conn.id,
            payload={"challenge_id": chal.id, "status": chal.status},
            created_by_id=getattr(current_user, "id", None),
        )
    )

    db.session.commit()
    return jsonify({"status": chal.status}), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Statement sync job
# ---------------------------------------------------------------------------


@bp.post("/connections/<int:connection_id>/sync")
@require_roles("finance", "admin")
def start_sync_job(connection_id: int):
    org_id = resolve_org_id()
    conn = BankConnection.query.filter_by(org_id=org_id, id=connection_id).first_or_404()

    payload = request.get_json(silent=True) or {}
    bank_account_id = payload.get("bank_account_id")
    from_raw = payload.get("from_date")
    to_raw = payload.get("to_date")

    if not bank_account_id:
        return jsonify({"error": "bank_account_id is required"}), HTTPStatus.BAD_REQUEST

    bank_account = BankAccount.query.filter_by(org_id=org_id, id=bank_account_id).first_or_404()

    from_date = date.fromisoformat(from_raw) if from_raw else date.today() - timedelta(days=7)
    to_date = date.fromisoformat(to_raw) if to_raw else date.today()

    job = BankSyncJob(
        org_id=org_id,
        connection_id=conn.id,
        bank_account_id=bank_account.id,
        status="pending",
        requested_from=from_date,
        requested_to=to_date,
        requested_by_id=getattr(current_user, "id", None),
    )
    db.session.add(job)
    db.session.flush()
    db.session.add(
        FinanceAuditLog(
            org_id=org_id,
            event_type="BANK_SYNC_JOB_CREATED",
            entity_type="BANK_SYNC_JOB",
            entity_id=job.id,
            payload={
                "connection": conn.name,
                "bank_account": bank_account.name,
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
            },
            created_by_id=getattr(current_user, "id", None),
        )
    )
    db.session.commit()

    try:
        if hasattr(celery_app, "send_task"):
            celery_app.send_task("erp.tasks.bank_sync.run_sync_job", args=[job.id])
        else:
            from erp.tasks import bank_sync as bank_sync_tasks

            bank_sync_tasks.run_sync_job(job.id)
    except Exception:
        job.status = "error"
        job.error_message = "Unable to dispatch sync task"
        job.finished_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"job_id": job.id, "status": job.status}), HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify({"job_id": job.id, "status": job.status}), HTTPStatus.ACCEPTED


@bp.get("/sync-jobs")
@require_roles("finance", "admin")
def list_sync_jobs():
    org_id = resolve_org_id()
    q = (
        BankSyncJob.query.filter_by(org_id=org_id)
        .options(joinedload(BankSyncJob.connection), joinedload(BankSyncJob.bank_account))
        .order_by(BankSyncJob.created_at.desc())
        .limit(100)
    )
    out = []
    for job in q.all():
        out.append(
            {
                "id": job.id,
                "status": job.status,
                "connection": job.connection.name if job.connection else None,
                "bank_account": job.bank_account.name if job.bank_account else None,
                "requested_from": job.requested_from.isoformat() if job.requested_from else None,
                "requested_to": job.requested_to.isoformat() if job.requested_to else None,
                "statements_created": job.statements_created,
                "lines_created": job.lines_created,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            }
        )
    return jsonify(out), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Cash-flow dashboard & simple forecasting
# ---------------------------------------------------------------------------


@bp.get("/cashflow")
@require_roles("finance", "admin")
def cashflow_dashboard():
    org_id = resolve_org_id()
    days = int(request.args.get("days", "60"))
    forecast_days = int(request.args.get("forecast_days", "30"))

    cutoff_date = datetime.utcnow().date() - timedelta(days=days)

    q = (
        db.session.query(
            BankStatementLine.tx_date,
            func.sum(BankStatementLine.amount).label("net_amount"),
        )
        .filter(
            BankStatementLine.org_id == org_id,
            BankStatementLine.tx_date >= cutoff_date,
        )
        .group_by(BankStatementLine.tx_date)
        .order_by(BankStatementLine.tx_date.asc())
    )

    history = []
    for tx_date, net in q.all():
        history.append({"date": tx_date.isoformat(), "net": float(net or 0)})

    if history:
        total_net = sum(Decimal(str(h["net"])) for h in history)
        avg_per_day = total_net / Decimal(len(history))
    else:
        avg_per_day = Decimal("0")

    forecast = []
    today = datetime.utcnow().date()
    for i in range(1, forecast_days + 1):
        d = today + timedelta(days=i)
        forecast.append({"date": d.isoformat(), "expected_net": float(avg_per_day)})

    return jsonify(
        {
            "history_days": days,
            "history": history,
            "forecast_days": forecast_days,
            "forecast": forecast,
        }
    ), HTTPStatus.OK
