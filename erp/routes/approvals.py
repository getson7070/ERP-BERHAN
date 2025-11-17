"""Approval workflow blueprint connecting orders with decision records."""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from erp.audit import log_audit
from erp.extensions import db
from erp.models import ApprovalRequest, Order
from erp.utils import resolve_org_id, role_required

bp = Blueprint("approvals", __name__, url_prefix="/approvals")


def _serialize(record: ApprovalRequest) -> dict[str, object]:
    return {
        "id": record.id,
        "order_id": record.order_id,
        "status": record.status,
        "requested_by": record.requested_by,
        "decided_by": record.decided_by,
        "decided_at": record.decided_at.isoformat() if record.decided_at else None,
        "notes": record.notes,
        "created_at": record.created_at.isoformat(),
    }


@bp.get("/requests")
@login_required
@role_required("Manager", "Admin")
def list_requests():
    """List approval requests for the active organisation."""

    org_id = resolve_org_id()
    records = (
        ApprovalRequest.query.filter_by(org_id=org_id)
        .order_by(ApprovalRequest.created_at.desc())
        .all()
    )
    return jsonify([_serialize(record) for record in records])


@bp.post("/orders/<int:order_id>")
@login_required
def request_order_approval(order_id: int):
    """Create an approval request for an order."""

    org_id = resolve_org_id()
    order = Order.query.filter_by(id=order_id, organization_id=org_id).first_or_404()
    existing = ApprovalRequest.query.filter_by(order_id=order.id, status="pending").first()
    if existing:
        return jsonify(_serialize(existing)), 200

    record = ApprovalRequest(
        org_id=org_id,
        order_id=order.id,
        requested_by=getattr(current_user, "id", None),
        status="pending",
        notes=request.json.get("notes") if request.is_json else None,
    )
    db.session.add(record)
    db.session.commit()
    log_audit(
        getattr(current_user, "id", None),
        org_id,
        "approval.requested",
        f"order={order.id}",
    )
    return jsonify(_serialize(record)), 201


@bp.post("/requests/<int:request_id>/decision")
@login_required
@role_required("Manager", "Admin")
def decide(request_id: int):
    """Approve or reject a pending request."""

    data = request.get_json(silent=True) or {}
    decision = data.get("decision", "").lower()
    hitl_token = data.get("hitl_token")
    if decision not in {"approved", "rejected"}:
        return jsonify({"error": "decision must be 'approved' or 'rejected'"}), 400
    if decision == "approved" and not hitl_token:
        return (
            jsonify({"error": "HITL confirmation token required for approvals"}),
            403,
        )

    record = ApprovalRequest.query.get_or_404(request_id)
    org_id = resolve_org_id()
    if record.org_id != org_id:
        return jsonify({"error": "request not in active organisation"}), 403
    if record.status != "pending":
        return jsonify({"error": "request already decided"}), 409

    record.status = decision
    record.decided_by = getattr(current_user, "id", None)
    record.decided_at = datetime.utcnow()
    record.notes = data.get("notes", record.notes)

    if record.order is not None:
        if decision == "approved":
            record.order.status = "approved"
        else:
            record.order.status = "rejected"

    db.session.commit()
    log_audit(
        getattr(current_user, "id", None),
        org_id,
        f"approval.{decision}",
        f"request={record.id};order={record.order_id};hitl={bool(hitl_token)}",
    )
    return jsonify(_serialize(record))


__all__ = ["bp", "list_requests", "request_order_approval", "decide"]
