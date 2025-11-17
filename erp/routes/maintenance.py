"""Maintenance ticket management blueprint."""
from __future__ import annotations

from datetime import datetime
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_login import login_required

from erp.audit import log_audit
from erp.extensions import db
from erp.models import MaintenanceTicket
from erp.utils import resolve_org_id, utc_now

bp = Blueprint("maintenance", __name__, url_prefix="/maintenance")


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.fromisoformat(value).date()
    except Exception:
        return None


def _serialize(ticket: MaintenanceTicket) -> dict[str, object]:
    return {
        "id": ticket.id,
        "asset_name": ticket.asset_name,
        "description": ticket.description,
        "severity": ticket.severity,
        "status": ticket.status,
        "due_date": ticket.due_date.isoformat() if ticket.due_date else None,
        "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
        "device_serial": ticket.device_serial,
        "installation_date": ticket.installation_date.isoformat()
        if ticket.installation_date
        else None,
        "warranty_expires_at": ticket.warranty_expires_at.isoformat()
        if ticket.warranty_expires_at
        else None,
        "site": {
            "label": ticket.site_label,
            "lat": ticket.site_lat,
            "lng": ticket.site_lng,
            "heartbeat_at": ticket.last_geo_heartbeat_at.isoformat()
            if ticket.last_geo_heartbeat_at
            else None,
        },
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
            due_date=_parse_date(payload.get("due_date")),
            device_serial=payload.get("device_serial"),
            installation_date=_parse_date(payload.get("installation_date")),
            warranty_expires_at=_parse_date(payload.get("warranty_expires_at")),
            site_label=payload.get("site_label"),
            site_lat=payload.get("site_lat"),
            site_lng=payload.get("site_lng"),
        )
        db.session.add(ticket)
        db.session.commit()
        log_audit(None, org_id, "maintenance.ticket_created", f"ticket={ticket.id};asset={asset}")
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
            ticket.closed_at = utc_now()
    if assigned_to is not None:
        ticket.assigned_to = assigned_to

    if "warranty_expires_at" in payload:
        ticket.warranty_expires_at = _parse_date(payload.get("warranty_expires_at"))

    db.session.commit()
    log_audit(None, org_id, "maintenance.ticket_updated", f"ticket={ticket.id};status={ticket.status}")
    return jsonify(_serialize(ticket))


@bp.post("/devices/<int:ticket_id>/heartbeat")
@login_required
def geo_heartbeat(ticket_id: int):
    org_id = resolve_org_id()
    ticket = MaintenanceTicket.query.filter_by(id=ticket_id, org_id=org_id).first_or_404()
    payload = request.get_json(silent=True) or {}
    ticket.site_lat = payload.get("lat")
    ticket.site_lng = payload.get("lng")
    ticket.site_label = payload.get("label", ticket.site_label)
    ticket.last_geo_heartbeat_at = utc_now()
    db.session.commit()
    log_audit(None, org_id, "maintenance.geo_heartbeat", f"ticket={ticket.id};lat={ticket.site_lat};lng={ticket.site_lng}")
    return jsonify(_serialize(ticket))


__all__ = ["bp", "tickets", "update_ticket", "geo_heartbeat"]
