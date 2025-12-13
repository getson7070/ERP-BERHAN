from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus

from flask import Blueprint, jsonify, request

from erp.extensions import db
from erp.models import BankAccount, BankConnection, BankSyncJob
from erp.security_decorators_phase2 import require_permission
from erp.services.banking_service import (
    create_or_update_access_token,
    create_two_factor_challenge as svc_create_2fa_challenge,
    verify_two_factor as svc_verify_2fa,
    start_sync as svc_start_sync,
)
from erp.utils import resolve_org_id

bp = Blueprint("banking_api", __name__, url_prefix="/api/banking")


@bp.get("/accounts")
@require_permission("banking", "view")
def list_bank_accounts():
    org_id = resolve_org_id()
    rows = BankAccount.query.filter_by(org_id=org_id).order_by(BankAccount.id.desc()).all()
    return jsonify([r.to_dict() for r in rows]), HTTPStatus.OK


@bp.post("/accounts")
@require_permission("banking", "manage")
def create_bank_account():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    account = BankAccount.from_payload(org_id, payload)
    db.session.add(account)
    db.session.commit()
    return jsonify(account.to_dict()), HTTPStatus.CREATED


@bp.get("/connections")
@require_permission("banking", "view")
def list_connections():
    org_id = resolve_org_id()
    rows = BankConnection.query.filter_by(org_id=org_id).order_by(BankConnection.id.desc()).all()
    return jsonify([r.to_dict() for r in rows]), HTTPStatus.OK


@bp.post("/connections")
@require_permission("banking", "manage")
def create_connection():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    conn = BankConnection.from_payload(org_id, payload)
    db.session.add(conn)
    db.session.commit()
    return jsonify(conn.to_dict()), HTTPStatus.CREATED


@bp.post("/connections/<int:connection_id>/tokens")
@require_permission("banking", "manage")
def upsert_access_token(connection_id: int):
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    token = create_or_update_access_token(org_id, connection_id, payload)
    return jsonify({"ok": True, "token_id": token.id}), HTTPStatus.OK


@bp.post("/connections/<int:connection_id>/2fa/challenge")
@require_permission("banking", "manage")
def create_two_factor_challenge(connection_id: int):
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    result = svc_create_2fa_challenge(org_id, connection_id, payload)
    return jsonify(result), HTTPStatus.OK


@bp.post("/connections/<int:connection_id>/2fa/verify")
@require_permission("banking", "manage")
def verify_two_factor(connection_id: int):
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    result = svc_verify_2fa(org_id, connection_id, payload)
    return jsonify(result), HTTPStatus.OK


@bp.post("/connections/<int:connection_id>/sync")
@require_permission("banking", "sync")
def start_sync_job(connection_id: int):
    org_id = resolve_org_id()
    job = svc_start_sync(org_id, connection_id)
    return jsonify({"ok": True, "job_id": job.id}), HTTPStatus.ACCEPTED


@bp.get("/sync-jobs")
@require_permission("banking", "view")
def list_sync_jobs():
    org_id = resolve_org_id()
    rows = BankSyncJob.query.filter_by(org_id=org_id).order_by(BankSyncJob.id.desc()).limit(500).all()
    return jsonify([r.to_dict() for r in rows]), HTTPStatus.OK


@bp.get("/cashflow")
@require_permission("banking", "view")
def cashflow_dashboard():
    org_id = resolve_org_id()
    # Preserve original behavior: let the model/service define dashboard contents
    data = BankSyncJob.cashflow_dashboard(org_id)
    return jsonify(data), HTTPStatus.OK
