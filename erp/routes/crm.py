"""CRM routes to capture leads and interactions."""
from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_login import login_required
from erp.security import require_roles, mfa_required

from erp.extensions import db
from erp.models import CrmInteraction, CrmLead
from erp.utils import resolve_org_id

bp = Blueprint("crm", __name__, url_prefix="/crm")


def _serialize_lead(lead: CrmLead) -> dict[str, object]:
    return {
        "id": lead.id,
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "status": lead.status,
        "potential_value": float(lead.potential_value or 0),
    }


@bp.route("/leads", methods=["GET", "POST"])
@login_required
@require_roles("crm", "sales", "admin", "management")
@mfa_required
def leads():
    org_id = resolve_org_id()
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        name = (payload.get("name") or "").strip()
        if not name:
            return jsonify({"error": "name is required"}), HTTPStatus.BAD_REQUEST

        lead = CrmLead(
            org_id=org_id,
            name=name,
            email=payload.get("email"),
            phone=payload.get("phone"),
            status=payload.get("status", "new"),
            potential_value=payload.get("potential_value"),
        )
        db.session.add(lead)
        db.session.commit()
        return jsonify(_serialize_lead(lead)), HTTPStatus.CREATED

    leads = CrmLead.query.filter_by(org_id=org_id).order_by(CrmLead.created_at.desc()).all()
    return jsonify([_serialize_lead(lead) for lead in leads])


@bp.post("/leads/<int:lead_id>/interactions")
@login_required
@require_roles("crm", "sales", "admin", "management")
@mfa_required
def add_interaction(lead_id: int):
    org_id = resolve_org_id()
    lead = CrmLead.query.filter_by(id=lead_id, org_id=org_id).first_or_404()
    payload = request.get_json(silent=True) or {}
    notes = (payload.get("notes") or "").strip()
    if not notes:
        return jsonify({"error": "notes required"}), HTTPStatus.BAD_REQUEST

    interaction = CrmInteraction(lead_id=lead.id, notes=notes, author_id=payload.get("author_id"))
    db.session.add(interaction)
    db.session.commit()
    return jsonify({
        "id": interaction.id,
        "notes": interaction.notes,
        "occurred_at": interaction.occurred_at.isoformat(),
    }), HTTPStatus.CREATED



