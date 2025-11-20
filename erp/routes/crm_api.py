"""CRM API endpoints for accounts, pipeline progression, and segmentation."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user
from sqlalchemy.orm import joinedload

from erp.extensions import db
from erp.models import CRMAccount, CRMContact, CRMPipelineEvent
from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("crm_api", __name__, url_prefix="/api/crm")


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------


def _serialize_contact(contact: CRMContact) -> dict[str, Any]:
    return {
        "id": contact.id,
        "full_name": contact.full_name,
        "role": contact.role,
        "email": contact.email,
        "phone": contact.phone,
        "is_primary": contact.is_primary,
    }


def _serialize_account(account: CRMAccount) -> dict[str, Any]:
    return {
        "id": account.id,
        "organization_id": account.organization_id,
        "code": account.code,
        "name": account.name,
        "account_type": account.account_type,
        "pipeline_stage": account.pipeline_stage,
        "segment": account.segment,
        "industry": account.industry,
        "country": account.country,
        "city": account.city,
        "is_active": account.is_active,
        "credit_limit": float(account.credit_limit or 0),
        "payment_terms_days": account.payment_terms_days,
        "created_at": account.created_at.isoformat(),
        "contacts": [_serialize_contact(c) for c in account.contacts],
    }


def _serialize_event(event: CRMPipelineEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "account_id": event.account_id,
        "from_stage": event.from_stage,
        "to_stage": event.to_stage,
        "reason": event.reason,
        "created_at": event.created_at.isoformat(),
        "created_by_id": event.created_by_id,
    }


# ---------------------------------------------------------------------------
# List / create / detail / update
# ---------------------------------------------------------------------------


@bp.get("/accounts")
@require_roles("crm", "sales", "admin")
def list_accounts():
    organization_id = resolve_org_id()
    stage = request.args.get("stage")
    segment = request.args.get("segment")

    query = CRMAccount.query.filter_by(organization_id=organization_id)

    if stage:
        query = query.filter(CRMAccount.pipeline_stage == stage)
    if segment:
        query = query.filter(CRMAccount.segment == segment)

    accounts = (
        query.options(joinedload(CRMAccount.contacts))
        .order_by(CRMAccount.name.asc())
        .limit(500)
        .all()
    )
    return jsonify([_serialize_account(acc) for acc in accounts]), HTTPStatus.OK


@bp.post("/accounts")
@require_roles("crm", "sales", "admin")
def create_account():
    organization_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), HTTPStatus.BAD_REQUEST

    account = CRMAccount(
        organization_id=organization_id,
        code=(payload.get("code") or "").strip() or None,
        name=name,
        account_type=(payload.get("account_type") or "customer").lower(),
        pipeline_stage=(payload.get("pipeline_stage") or "lead").lower(),
        segment=(payload.get("segment") or "").strip() or None,
        industry=(payload.get("industry") or "").strip() or None,
        country=(payload.get("country") or "").strip() or None,
        city=(payload.get("city") or "").strip() or None,
        credit_limit=payload.get("credit_limit") or 0,
        payment_terms_days=payload.get("payment_terms_days"),
        created_by_id=getattr(current_user, "id", None),
    )

    primary_contact = payload.get("primary_contact") or {}
    full_name = (primary_contact.get("full_name") or "").strip()
    if full_name:
        contact = CRMContact(
            organization_id=organization_id,
            full_name=full_name,
            role=(primary_contact.get("role") or "").strip() or None,
            email=(primary_contact.get("email") or "").strip() or None,
            phone=(primary_contact.get("phone") or "").strip() or None,
            is_primary=True,
        )
        account.contacts.append(contact)

    db.session.add(account)
    db.session.commit()
    return jsonify(_serialize_account(account)), HTTPStatus.CREATED


@bp.get("/accounts/<int:account_id>")
@require_roles("crm", "sales", "admin")
def account_detail(account_id: int):
    organization_id = resolve_org_id()
    account = (
        CRMAccount.query.filter_by(organization_id=organization_id, id=account_id)
        .options(joinedload(CRMAccount.contacts))
        .first_or_404()
    )
    return jsonify(_serialize_account(account)), HTTPStatus.OK


@bp.patch("/accounts/<int:account_id>")
@require_roles("crm", "sales", "admin")
def update_account(account_id: int):
    organization_id = resolve_org_id()
    account = CRMAccount.query.filter_by(organization_id=organization_id, id=account_id).first_or_404()

    payload = request.get_json(silent=True) or {}
    for field in (
        "name",
        "account_type",
        "segment",
        "industry",
        "country",
        "city",
        "credit_limit",
        "payment_terms_days",
    ):
        if field in payload:
            setattr(account, field, payload[field])

    if "is_active" in payload:
        account.is_active = bool(payload["is_active"])

    db.session.commit()
    return jsonify(_serialize_account(account)), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Pipeline transitions (lead -> prospect -> client)
# ---------------------------------------------------------------------------


_ALLOWED_STAGES = ("lead", "prospect", "client")


def _next_stage(current: str) -> str | None:
    try:
        idx = _ALLOWED_STAGES.index(current)
    except ValueError:
        return None
    if idx + 1 < len(_ALLOWED_STAGES):
        return _ALLOWED_STAGES[idx + 1]
    return None


@bp.post("/accounts/<int:account_id>/advance-stage")
@require_roles("crm", "sales", "admin")
def advance_stage(account_id: int):
    organization_id = resolve_org_id()
    account = (
        CRMAccount.query.filter_by(organization_id=organization_id, id=account_id)
        .with_for_update()
        .first_or_404()
    )

    current_stage = account.pipeline_stage
    next_stage = _next_stage(current_stage)
    if not next_stage:
        return jsonify({"error": f"cannot advance from stage {current_stage}"}), HTTPStatus.BAD_REQUEST

    payload = request.get_json(silent=True) or {}
    reason = (payload.get("reason") or "").strip() or None

    account.pipeline_stage = next_stage
    event = CRMPipelineEvent(
        organization_id=organization_id,
        account_id=account.id,
        from_stage=current_stage,
        to_stage=next_stage,
        reason=reason,
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(event)
    db.session.commit()

    return jsonify({"account": _serialize_account(account), "event": _serialize_event(event)}), HTTPStatus.OK


@bp.get("/accounts/<int:account_id>/pipeline-events")
@require_roles("crm", "sales", "admin")
def pipeline_events(account_id: int):
    organization_id = resolve_org_id()
    events = (
        CRMPipelineEvent.query.filter_by(organization_id=organization_id, account_id=account_id)
        .order_by(CRMPipelineEvent.created_at.desc())
        .limit(100)
        .all()
    )
    return jsonify([_serialize_event(event) for event in events]), HTTPStatus.OK
