"""Dynamic role request/approval endpoints."""

from __future__ import annotations

from datetime import datetime
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.extensions import db
from erp.models import RoleAssignmentRequest
from erp.security import require_roles
from erp.security_rbac_phase2 import role_dominates
from erp.services.role_service import grant_role_to_user
from erp.utils import resolve_org_id

bp = Blueprint("role_request_api", __name__, url_prefix="/api/rbac/role-requests")


@bp.post("")
def create_request():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    if not payload.get("role_key"):
        return jsonify({"error": "role_key_required"}), HTTPStatus.BAD_REQUEST

    req = RoleAssignmentRequest(
        org_id=org_id,
        requester_id=getattr(current_user, "id", None),
        target_user_id=payload.get("target_user_id") or getattr(current_user, "id", None),
        role_key=payload.get("role_key"),
        reason=payload.get("reason"),
    )
    db.session.add(req)
    db.session.commit()
    return jsonify({"id": req.id, "status": req.status}), HTTPStatus.CREATED


@bp.get("")
@require_roles("admin", "superadmin", "hr")
def list_requests():
    org_id = resolve_org_id()
    rows = (
        RoleAssignmentRequest.query.filter_by(org_id=org_id)
        .order_by(RoleAssignmentRequest.id.desc())
        .limit(500)
        .all()
    )
    return (
        jsonify(
            [
                {
                    "id": r.id,
                    "requester_id": r.requester_id,
                    "target_user_id": r.target_user_id,
                    "role_key": r.role_key,
                    "reason": r.reason,
                    "status": r.status,
                }
                for r in rows
            ]
        ),
        HTTPStatus.OK,
    )


@bp.post("/<int:req_id>/approve")
@require_roles("admin", "superadmin")
def approve_request(req_id: int):
    org_id = resolve_org_id()
    req = RoleAssignmentRequest.query.filter_by(org_id=org_id, id=req_id).first_or_404()
    if req.status != "pending":
        return jsonify({"error": "not_pending"}), HTTPStatus.BAD_REQUEST

    # Ensure approver cannot grant higher roles than allowed
    approver_roles = getattr(current_user, "roles", []) or []
    dominant_role = "superadmin" if "superadmin" in approver_roles else "admin"
    if not role_dominates(org_id, dominant_role, req.role_key):
        return jsonify({"error": "cannot_assign_higher_role"}), HTTPStatus.FORBIDDEN

    grant_role_to_user(
        org_id=org_id,
        user_id=req.target_user_id,
        role_key=req.role_key,
        acting_user=current_user,
    )

    req.status = "approved"
    req.reviewed_by_id = getattr(current_user, "id", None)
    req.reviewed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"status": "approved"}), HTTPStatus.OK


@bp.post("/<int:req_id>/reject")
@require_roles("admin", "superadmin")
def reject_request(req_id: int):
    org_id = resolve_org_id()
    req = RoleAssignmentRequest.query.filter_by(org_id=org_id, id=req_id).first_or_404()
    if req.status != "pending":
        return jsonify({"error": "not_pending"}), HTTPStatus.BAD_REQUEST

    req.status = "rejected"
    req.reviewed_by_id = getattr(current_user, "id", None)
    req.reviewed_at = datetime.utcnow()
    req.review_note = (request.get_json(silent=True) or {}).get("note")
    db.session.commit()
    return jsonify({"status": "rejected"}), HTTPStatus.OK


__all__ = ["bp"]
