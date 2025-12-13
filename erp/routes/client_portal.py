"""Client portal API.

All endpoints here are institution-scoped.
A client may have multiple contacts under the same Institution (TIN),
but must never see data outside their Institution.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.extensions import db
from erp.models import Order, MaintenanceWorkOrder, ClientAccount
from erp.security_decorators_phase2 import require_permission

bp = Blueprint("client_portal", __name__, url_prefix="/api/client-portal")


def _client_institution_id() -> int | None:
    """Return institution_id for the logged-in client."""
    if not current_user or not getattr(current_user, "is_authenticated", False):
        return None
    return getattr(current_user, "institution_id", None)


def _ensure_client_context():
    inst_id = _client_institution_id()
    if inst_id is None:
        return (
            jsonify({"error": "client_not_authenticated_or_unlinked"}),
            HTTPStatus.FORBIDDEN,
        )
    return inst_id


def _serialize_order(order: Order) -> dict[str, Any]:
    return {
        "id": order.id,
        "status": order.status,
        "payment_status": getattr(order, "payment_status", None),
        "total_amount": str(order.total_amount),
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }


def _serialize_maintenance(m: MaintenanceWorkOrder) -> dict[str, Any]:
    return {
        "id": m.id,
        "status": m.status,
        "priority": m.priority,
        "asset_name": getattr(m, "asset_name", None),
        "reported_issue": m.reported_issue,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "updated_at": m.updated_at.isoformat() if m.updated_at else None,
    }


# -------------------------------------------------------------------
# Dashboard
# -------------------------------------------------------------------

@bp.get("/dashboard")
@require_permission("client_portal", "view")
def dashboard():
    inst_id = _ensure_client_context()
    if not isinstance(inst_id, int):
        return inst_id

    orders_count = (
        db.session.query(Order)
        .filter(Order.institution_id == inst_id)
        .count()
    )

    open_maintenance = (
        db.session.query(MaintenanceWorkOrder)
        .filter(MaintenanceWorkOrder.institution_id == inst_id)
        .filter(MaintenanceWorkOrder.status.notin_(["closed", "completed"]))
        .count()
    )

    return (
        jsonify(
            {
                "orders_total": orders_count,
                "maintenance_open": open_maintenance,
            }
        ),
        HTTPStatus.OK,
    )


# -------------------------------------------------------------------
# Orders
# -------------------------------------------------------------------

@bp.get("/orders")
@require_permission("orders", "view")
def list_orders():
    inst_id = _ensure_client_context()
    if not isinstance(inst_id, int):
        return inst_id

    orders = (
        Order.query.filter_by(institution_id=inst_id)
        .order_by(Order.id.desc())
        .limit(200)
        .all()
    )

    return jsonify([_serialize_order(o) for o in orders]), HTTPStatus.OK


@bp.post("/orders")
@require_permission("orders", "create")
def create_order():
    inst_id = _ensure_client_context()
    if not isinstance(inst_id, int):
        return inst_id

    payload = request.get_json(silent=True) or {}
    items = payload.get("items") or []

    if not items:
        return jsonify({"error": "items_required"}), HTTPStatus.BAD_REQUEST

    order = Order(
        institution_id=inst_id,
        organization_id=current_user.org_id,
        initiator_type="client",
        initiator_id=current_user.id,
        status="submitted",
        payment_status="unpaid",
        commission_enabled=False,
    )

    db.session.add(order)
    db.session.commit()

    return jsonify(_serialize_order(order)), HTTPStatus.CREATED


# -------------------------------------------------------------------
# Maintenance
# -------------------------------------------------------------------

@bp.get("/maintenance")
@require_permission("maintenance_work_orders", "view")
def list_maintenance():
    inst_id = _ensure_client_context()
    if not isinstance(inst_id, int):
        return inst_id

    records = (
        MaintenanceWorkOrder.query.filter_by(institution_id=inst_id)
        .order_by(MaintenanceWorkOrder.id.desc())
        .limit(200)
        .all()
    )

    return jsonify([_serialize_maintenance(m) for m in records]), HTTPStatus.OK


@bp.post("/maintenance")
@require_permission("maintenance_work_orders", "create")
def create_maintenance():
    inst_id = _ensure_client_context()
    if not isinstance(inst_id, int):
        return inst_id

    payload = request.get_json(silent=True) or {}
    issue = (payload.get("reported_issue") or "").strip()
    priority = (payload.get("priority") or "normal").strip().lower()

    if not issue:
        return jsonify({"error": "reported_issue_required"}), HTTPStatus.BAD_REQUEST

    wo = MaintenanceWorkOrder(
        institution_id=inst_id,
        organization_id=current_user.org_id,
        reported_issue=issue,
        priority=priority,
        status="open",
        requested_by_client_id=current_user.id,
    )

    db.session.add(wo)
    db.session.commit()

    return jsonify(_serialize_maintenance(wo)), HTTPStatus.CREATED


# -------------------------------------------------------------------
# Profile
# -------------------------------------------------------------------

@bp.get("/me")
@require_permission("client_portal", "view")
def me():
    acc: ClientAccount = current_user  # type: ignore
    return (
        jsonify(
            {
                "id": acc.id,
                "email": acc.email,
                "phone": acc.phone,
                "contact_name": acc.contact_name,
                "contact_position": acc.contact_position,
                "institution_id": acc.institution_id,
            }
        ),
        HTTPStatus.OK,
    )
