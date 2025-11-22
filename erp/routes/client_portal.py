"""Client portal endpoints for self-service account and ticket access."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.extensions import db
from erp.models import CRMAccount, ClientPortalLink, SupportTicket
from erp.security import require_login
from erp.utils import resolve_org_id

bp = Blueprint("client_portal_api", __name__, url_prefix="/api/portal")


def _serialize_account(account: CRMAccount) -> dict[str, Any]:
    return {
        "id": account.id,
        "name": account.name,
        "account_type": account.account_type,
        "pipeline_stage": account.pipeline_stage,
        "segment": account.segment,
        "country": account.country,
        "city": account.city,
        "credit_limit": float(account.credit_limit or 0),
        "payment_terms_days": account.payment_terms_days,
    }


def _serialize_ticket(ticket: SupportTicket) -> dict[str, Any]:
    return {
        "id": ticket.id,
        "subject": ticket.subject,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat(),
    }


def _get_portal_account(organization_id: int) -> CRMAccount:
    if not current_user.is_authenticated:
        raise RuntimeError("Unauthenticated access")

    link = ClientPortalLink.query.filter_by(
        organization_id=organization_id, user_id=current_user.id
    ).first()
    if not link:
        from flask import abort

        abort(HTTPStatus.FORBIDDEN)

    account = CRMAccount.query.filter_by(
        organization_id=organization_id, id=link.account_id
    ).first()
    if not account:
        from flask import abort

        abort(HTTPStatus.NOT_FOUND)
    return account


@bp.get("/me/account")
@require_login
def me_account():
    organization_id = resolve_org_id()
    account = _get_portal_account(organization_id)
    return jsonify(_serialize_account(account)), HTTPStatus.OK


@bp.get("/me/tickets")
@require_login
def me_tickets():
    organization_id = resolve_org_id()
    account = _get_portal_account(organization_id)
    tickets = (
        SupportTicket.query.filter_by(organization_id=organization_id, account_id=account.id)
        .order_by(SupportTicket.created_at.desc())
        .all()
    )
    return jsonify([_serialize_ticket(ticket) for ticket in tickets]), HTTPStatus.OK


@bp.post("/me/tickets")
@require_login
def me_create_ticket():
    organization_id = resolve_org_id()
    account = _get_portal_account(organization_id)

    payload = request.get_json(silent=True) or {}
    subject = (payload.get("subject") or "").strip()
    if not subject:
        return jsonify({"error": "subject is required"}), HTTPStatus.BAD_REQUEST

    ticket = SupportTicket(
        organization_id=organization_id,
        account_id=account.id,
        subject=subject,
        description=(payload.get("description") or "").strip() or None,
        priority=(payload.get("priority") or "normal").lower(),
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(ticket)
    db.session.commit()
    return jsonify(_serialize_ticket(ticket)), HTTPStatus.CREATED
