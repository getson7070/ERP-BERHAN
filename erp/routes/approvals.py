"""Approval workflow blueprint connecting orders with decision records."""
from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.audit import log_audit
from erp.extensions import db
from erp.models import ApprovalRequest, Order
from erp.security_decorators_phase2 import require_permission
from erp.utils import resolve_org_id

bp = Blueprint("approvals", __name__, url_prefix="/approvals")


def _serialize(record: ApprovalRequest) -> dict[str, Any]:
    return {
        "id": record.id,
        "org_id": record.org_id,
        "order_id": record.order_id,
        "status": record.status,
        "requested_by": record.requested_by,
        "decided_by": record.decided_by,
        "decided_at": record.decided_at.isoformat() if record.decided_at else None,
        "notes": record.notes,
        "created_at": record.created_at.isoformat() if getattr(record, "created_at", None) else None,
        "updated_at": record.updated_at.isoformat() if getattr(record, "updated_at", None) else None,
    }


@bp.get("/")
@require_permission("approvals", "view")
def list_requests():
    org_id = resolve_org_id()
    status = (request.args.get("status") or "pending").strip().lower()

    q = ApprovalRequest.query.filter_by(org_id=org_id)
    if status in {"pending", "approved", "rejected"}:
        q = q.filter_by(status=status)

    records = q.order_by(ApprovalRequest.id.desc()).limit(300).all()
    return jsonify([_serialize(r) for r in records]), HTTPStatus.OK


@bp.post("/orders/<int:order_id>/request")
@require_permission("approvals", "request")
def request_order_approval(order_id: int):
    org_id = resolve_org_id()
    order = Order.query.filter_by(id=order_id, organization_id=org_id).first()
    if order is None:
        return jsonify({"error": "order_not_found"}), HTTPStatus.NOT_FOUND

    # Avoid duplicate pending requests for the same order
    existing = (
        ApprovalRequest.query.filter_by(org_id=org_id, order_id=order.id, status="pending")
        .order_by(ApprovalRequest.id.desc())
        .first()
    )
    if existing:
        return jsonify(_serialize(existing)), HTTPStatus.OK

    payload = request.get_json(silent=True) or {}
    notes = (payload.get("notes") or "").strip()

    record = ApprovalRequest(
        org_id=org_id,
        order_id=order.id,
        status="pending",
        requested_by=getattr(current_user, "id", None),
        notes=notes or None,
    )
    db.session.add(record)
    db.session.commit()

    log_audit(
        getattr(current_user, "id", None),
        org_id,
        "approval.requested",
        f"request={record.id};order={record.order_id}",
    )
    return jsonify(_serialize(record)), HTTPStatus.CREATED


@bp.post("/<int:request_id>/decide")
@require_permission("approvals", "decide")
def decide(request_id: int):
    """Approve or reject a pending approval request.

    Payload:
      - decision: "approve" | "reject"
      - notes: optional
      - hitl_token: optional (logged for traceability)
    """
    org_id = resolve_org_id()
    record = ApprovalRequest.query.filter_by(org_id=org_id, id=request_id).first()
    if record is None:
        return jsonify({"error": "request_not_found"}), HTTPStatus.NOT_FOUND

    if record.status != "pending":
        return jsonify(_serialize(record)), HTTPStatus.OK

    payload = request.get_json(silent=True) or {}
    decision = (payload.get("decision") or "").strip().lower()
    notes = (payload.get("notes") or "").strip() or None
    hitl_token = (payload.get("hitl_token") or "").strip() or None

    if decision not in {"approve", "reject"}:
        return jsonify({"error": "decision must be approve|reject"}), HTTPStatus.BAD_REQUEST

    record.decided_by = getattr(current_user, "id", None)
    record.decided_at = datetime.now(UTC)
    record.notes = notes
    record.status = "approved" if decision == "approve" else "rejected"

    # Update linked order status if present
    if record.order_id:
        order = Order.query.filter_by(id=record.order_id, organization_id=org_id).first()
        if order is not None:
            if decision == "approve":
                # Preserve model behavior: use set_status if present
                if hasattr(order, "set_status"):
                    order.set_status("approved")
                else:
                    order.status = "approved"
            else:
                if hasattr(order, "set_status"):
                    order.set_status("rejected")
                else:
                    order.status = "rejected"

    db.session.commit()

    log_audit(
        getattr(current_user, "id", None),
        org_id,
        f"approval.{decision}",
        f"request={record.id};order={record.order_id};hitl={bool(hitl_token)}",
    )
    return jsonify(_serialize(record)), HTTPStatus.OK


__all__ = ["bp", "list_requests", "request_order_approval", "decide"]
