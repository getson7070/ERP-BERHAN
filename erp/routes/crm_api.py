from __future__ import annotations

from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request

from erp.models import CRMAccount, CRMContact, CRMPipelineEvent
from erp.security_decorators_phase2 import require_permission
from erp.utils import resolve_org_id

bp = Blueprint("crm_api", __name__, url_prefix="/api/crm")


def _serialize_account(account: CRMAccount) -> dict[str, Any]:
    return {
        "id": account.id,
        "name": account.name,
        "stage": account.stage,
        "owner_user_id": account.owner_user_id,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None,
    }


def _serialize_contact(contact: CRMContact) -> dict[str, Any]:
    return {
        "id": contact.id,
        "account_id": contact.account_id,
        "full_name": contact.full_name,
        "phone": contact.phone,
        "email": contact.email,
        "position": contact.position,
        "created_at": contact.created_at.isoformat() if contact.created_at else None,
    }


def _serialize_event(event: CRMPipelineEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "account_id": event.account_id,
        "event_type": event.event_type,
        "from_stage": event.from_stage,
        "to_stage": event.to_stage,
        "message": event.message,
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "created_by_id": event.created_by_id,
    }


@bp.get("/accounts")
@require_permission("crm", "view")
def list_accounts():
    organization_id = resolve_org_id()
    accounts = (
        CRMAccount.query.filter_by(organization_id=organization_id)
        .order_by(CRMAccount.updated_at.desc())
        .limit(200)
        .all()
    )
    return jsonify([_serialize_account(a) for a in accounts]), HTTPStatus.OK


@bp.post("/accounts")
@require_permission("crm", "manage")
def create_account():
    organization_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), HTTPStatus.BAD_REQUEST

    account = CRMAccount(
        organization_id=organization_id,
        name=name,
        stage=(payload.get("stage") or "lead").strip(),
        owner_user_id=payload.get("owner_user_id"),
    )
    CRMAccount.add_default_contacts(account, payload)

    CRMAccount.add_create_event(account, payload)

    from erp.extensions import db  # local import to avoid circulars
    db.session.add(account)
    db.session.commit()

    return jsonify(_serialize_account(account)), HTTPStatus.CREATED


@bp.get("/accounts/<int:account_id>")
@require_permission("crm", "view")
def account_detail(account_id: int):
    organization_id = resolve_org_id()
    account = CRMAccount.query.filter_by(organization_id=organization_id, id=account_id).first()
    if account is None:
        return jsonify({"error": "not_found"}), HTTPStatus.NOT_FOUND

    contacts = CRMContact.query.filter_by(organization_id=organization_id, account_id=account.id).all()
    return (
        jsonify({"account": _serialize_account(account), "contacts": [_serialize_contact(c) for c in contacts]}),
        HTTPStatus.OK,
    )


@bp.patch("/accounts/<int:account_id>")
@require_permission("crm", "manage")
def update_account(account_id: int):
    organization_id = resolve_org_id()
    account = CRMAccount.query.filter_by(organization_id=organization_id, id=account_id).first()
    if account is None:
        return jsonify({"error": "not_found"}), HTTPStatus.NOT_FOUND

    payload = request.get_json(silent=True) or {}
    if "name" in payload:
        account.name = (payload.get("name") or "").strip()
    if "stage" in payload:
        account.stage = (payload.get("stage") or "").strip()
    if "owner_user_id" in payload:
        account.owner_user_id = payload.get("owner_user_id")

    from erp.extensions import db
    db.session.commit()

    return jsonify(_serialize_account(account)), HTTPStatus.OK


@bp.post("/accounts/<int:account_id>/advance-stage")
@require_permission("crm", "manage")
def advance_stage(account_id: int):
    organization_id = resolve_org_id()
    account = CRMAccount.query.filter_by(organization_id=organization_id, id=account_id).first()
    if account is None:
        return jsonify({"error": "not_found"}), HTTPStatus.NOT_FOUND

    payload = request.get_json(silent=True) or {}
    to_stage = (payload.get("to_stage") or "").strip()
    if not to_stage:
        return jsonify({"error": "to_stage is required"}), HTTPStatus.BAD_REQUEST

    from_stage = account.stage
    account.stage = to_stage

    event = CRMPipelineEvent(
        organization_id=organization_id,
        account_id=account.id,
        event_type="stage_change",
        from_stage=from_stage,
        to_stage=to_stage,
        message=(payload.get("message") or "").strip(),
        created_by_id=payload.get("created_by_id"),
    )

    from erp.extensions import db
    db.session.add(event)
    db.session.commit()

    return jsonify({"ok": True, "account": _serialize_account(account)}), HTTPStatus.OK


@bp.get("/accounts/<int:account_id>/pipeline-events")
@require_permission("crm", "view")
def pipeline_events(account_id: int):
    organization_id = resolve_org_id()
    events = (
        CRMPipelineEvent.query.filter_by(organization_id=organization_id, account_id=account_id)
        .order_by(CRMPipelineEvent.created_at.desc())
        .limit(100)
        .all()
    )
    return jsonify([_serialize_event(event) for event in events]), HTTPStatus.OK
