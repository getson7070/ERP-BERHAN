"""Maintenance ticket management blueprint."""
from __future__ import annotations

from datetime import datetime
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_login import login_required

from erp.extensions import db
from erp.models import MaintenanceTicket
from erp.utils import resolve_org_id

bp = Blueprint("maintenance", __name__, url_prefix="/maintenance")


def _serialize(ticket: MaintenanceTicket) -> dict[str, object]:
    return {
        "id": ticket.id,
        "asset_name": ticket.asset_name,
        "description": ticket.description,
        "severity": ticket.severity,
        "status": ticket.status,
        "due_date": ticket.due_date.isoformat() if ticket.due_date else None,
        "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
    }


@bp.route("/tickets", methods=["GET", "POST"])
@login_required
def tickets():
    org_id = resolve_org_id()
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        asset = (payload.get("asset_name") or "").strip()
        description = (payload.get("description") or "").strip()
        if not asset or not description:
            return jsonify({"error": "asset_name and description required"}), HTTPStatus.BAD_REQUEST

        ticket = MaintenanceTicket(
            org_id=org_id,
            asset_name=asset,
            description=description,
            severity=payload.get("severity", "medium"),
            due_date=payload.get("due_date"),
        )
        db.session.add(ticket)
        db.session.commit()
        return jsonify(_serialize(ticket)), HTTPStatus.CREATED

    records = (
        MaintenanceTicket.query.filter_by(org_id=org_id)
        .order_by(MaintenanceTicket.created_at.desc())
        .all()
    )
    return jsonify([_serialize(ticket) for ticket in records])


@bp.patch("/tickets/<int:ticket_id>")
@login_required
def update_ticket(ticket_id: int):
    payload = request.get_json(silent=True) or {}
    org_id = resolve_org_id()
    ticket = MaintenanceTicket.query.filter_by(id=ticket_id, org_id=org_id).first_or_404()
    status = payload.get("status")
    assigned_to = payload.get("assigned_to")
    if status:
        ticket.status = status
        if status == "closed":
            ticket.closed_at = datetime.utcnow()
    if assigned_to is not None:
        ticket.assigned_to = assigned_to

    db.session.commit()
    return jsonify(_serialize(ticket))


__all__ = ["bp", "tickets", "update_ticket"]
