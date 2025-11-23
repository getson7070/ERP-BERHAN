"""Procurement workflows: purchase orders, approvals, receipts, and returns."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user
from sqlalchemy.orm import joinedload

from erp.extensions import db
from erp.models import PurchaseOrder, PurchaseOrderLine
from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("procurement_api", __name__, url_prefix="/api/procurement")


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------


def _serialize_line(line: PurchaseOrderLine) -> dict[str, Any]:
    return {
        "id": line.id,
        "item_code": line.item_code,
        "item_description": line.item_description,
        "ordered_quantity": float(line.ordered_quantity or 0),
        "received_quantity": float(line.received_quantity or 0),
        "returned_quantity": float(line.returned_quantity or 0),
        "unit_price": float(line.unit_price or 0),
        "tax_rate": float(line.tax_rate or 0),
    }


def _serialize_order(order: PurchaseOrder) -> dict[str, Any]:
    return {
        "id": order.id,
        "organization_id": order.organization_id,
        "supplier_id": order.supplier_id,
        "supplier_name": order.supplier_name,
        "status": order.status,
        "currency": order.currency,
        "total_amount": float(order.total_amount or 0),
        "created_at": order.created_at.isoformat(),
        "created_by_id": order.created_by_id,
        "approved_at": order.approved_at.isoformat() if order.approved_at else None,
        "approved_by_id": order.approved_by_id,
        "cancelled_at": order.cancelled_at.isoformat() if order.cancelled_at else None,
        "cancelled_by_id": order.cancelled_by_id,
        "cancel_reason": order.cancel_reason,
        "lines": [_serialize_line(line) for line in order.lines],
    }


def _parse_decimal(value: Any, default: str = "0") -> Decimal:
    if value is None or value == "":
        return Decimal(default)
    return Decimal(str(value))


# ---------------------------------------------------------------------------
# Create / list / detail
# ---------------------------------------------------------------------------


@bp.get("/orders")
@require_roles("procurement", "inventory", "admin")
def list_orders():
    """List purchase orders for the current organisation."""

    organization_id = resolve_org_id()
    query = (
        PurchaseOrder.query.filter_by(organization_id=organization_id)
        .options(joinedload(PurchaseOrder.lines))
        .order_by(PurchaseOrder.created_at.desc())
        .limit(200)
    )
    return jsonify([_serialize_order(po) for po in query.all()])


@bp.post("/orders")
@require_roles("procurement", "inventory", "admin")
def create_order():
    """Create a new purchase order and associated lines."""

    organization_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    supplier_id = payload.get("supplier_id")
    supplier_name = (payload.get("supplier_name") or "").strip()
    currency = (payload.get("currency") or "ETB").upper()
    lines_payload = payload.get("lines") or []

    if not lines_payload:
        return jsonify({"error": "at least one line is required"}), HTTPStatus.BAD_REQUEST

    po = PurchaseOrder(
        organization_id=organization_id,
        supplier_id=supplier_id,
        supplier_name=supplier_name or None,
        currency=currency,
        status="draft",
        created_by_id=getattr(current_user, "id", None),
    )

    for raw in lines_payload:
        item_code = (raw.get("item_code") or "").strip()
        if not item_code:
            return jsonify({"error": "item_code is required for each line"}), HTTPStatus.BAD_REQUEST

        ordered_quantity = _parse_decimal(raw.get("ordered_quantity"), default="0")
        if ordered_quantity <= 0:
            return jsonify({"error": "ordered_quantity must be > 0"}), HTTPStatus.BAD_REQUEST

        line = PurchaseOrderLine(
            organization_id=organization_id,
            item_code=item_code,
            item_description=(raw.get("item_description") or "").strip() or None,
            ordered_quantity=ordered_quantity,
            unit_price=_parse_decimal(raw.get("unit_price"), default="0"),
            tax_rate=_parse_decimal(raw.get("tax_rate"), default="0"),
        )
        po.lines.append(line)

    po.recalc_totals()
    db.session.add(po)
    db.session.commit()

    return jsonify(_serialize_order(po)), HTTPStatus.CREATED


@bp.get("/orders/<int:order_id>")
@require_roles("procurement", "inventory", "admin")
def order_detail(order_id: int):
    organization_id = resolve_org_id()
    po = (
        PurchaseOrder.query.filter_by(organization_id=organization_id, id=order_id)
        .options(joinedload(PurchaseOrder.lines))
        .first_or_404()
    )
    return jsonify(_serialize_order(po))


# ---------------------------------------------------------------------------
# Status changes: submit / approve / cancel
# ---------------------------------------------------------------------------


@bp.post("/orders/<int:order_id>/submit")
@require_roles("procurement", "inventory", "admin")
def submit_order(order_id: int):
    """Move a draft order into the submitted state."""

    organization_id = resolve_org_id()
    po = (
        PurchaseOrder.query.filter_by(organization_id=organization_id, id=order_id)
        .with_for_update()
        .first_or_404()
    )

    if po.status != "draft":
        return (
            jsonify({"error": f"cannot submit order in status {po.status}"}),
            HTTPStatus.BAD_REQUEST,
        )

    po.status = "submitted"
    db.session.commit()
    return jsonify(_serialize_order(po))


@bp.post("/orders/<int:order_id>/approve")
@require_roles("procurement", "admin")
def approve_order(order_id: int):
    """Approve a submitted order."""

    organization_id = resolve_org_id()
    po = (
        PurchaseOrder.query.filter_by(organization_id=organization_id, id=order_id)
        .with_for_update()
        .options(joinedload(PurchaseOrder.lines))
        .first_or_404()
    )

    if po.status not in {"submitted", "draft"}:
        return (
            jsonify({"error": f"cannot approve order in status {po.status}"}),
            HTTPStatus.BAD_REQUEST,
        )

    po.status = "approved"
    po.approved_at = datetime.now(UTC)
    po.approved_by_id = getattr(current_user, "id", None)

    db.session.commit()
    return jsonify(_serialize_order(po))


@bp.post("/orders/<int:order_id>/cancel")
@require_roles("procurement", "admin")
def cancel_order(order_id: int):
    """Cancel an order that has not yet been received."""

    organization_id = resolve_org_id()
    po = (
        PurchaseOrder.query.filter_by(organization_id=organization_id, id=order_id)
        .with_for_update()
        .first_or_404()
    )

    if not po.can_cancel():
        return (
            jsonify({"error": f"cannot cancel order in status {po.status}"}),
            HTTPStatus.BAD_REQUEST,
        )

    payload = request.get_json(silent=True) or {}
    reason = (payload.get("reason") or "").strip()

    po.status = "cancelled"
    po.cancelled_at = datetime.now(UTC)
    po.cancelled_by_id = getattr(current_user, "id", None)
    po.cancel_reason = reason or None

    db.session.commit()
    return jsonify(_serialize_order(po))


# ---------------------------------------------------------------------------
# Receipts (partial deliveries)
# ---------------------------------------------------------------------------


@bp.post("/orders/<int:order_id>/receive")
@require_roles("procurement", "inventory", "admin")
def receive_goods(order_id: int):
    """Record a partial or full goods receipt for one or more lines."""

    organization_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    lines_payload = payload.get("lines") or []

    if not lines_payload:
        return jsonify({"error": "lines payload is required"}), HTTPStatus.BAD_REQUEST

    po = (
        PurchaseOrder.query.filter_by(organization_id=organization_id, id=order_id)
        .with_for_update()
        .options(joinedload(PurchaseOrder.lines))
        .first_or_404()
    )

    if not po.can_receive():
        return (
            jsonify({"error": f"cannot receive goods in status {po.status}"}),
            HTTPStatus.BAD_REQUEST,
        )

    lines_by_id = {line.id: line for line in po.lines}

    try:
        for raw in lines_payload:
            line_id = raw.get("line_id")
            quantity = _parse_decimal(raw.get("quantity"), default="0")
            if not line_id or quantity <= 0:
                raise ValueError("line_id and positive quantity are required")

            line = lines_by_id.get(int(line_id))
            if line is None:
                raise ValueError(f"invalid line_id {line_id}")

            line.receive(quantity)
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

    po.update_status_from_lines()
    db.session.commit()
    return jsonify(_serialize_order(po))


# ---------------------------------------------------------------------------
# Returns
# ---------------------------------------------------------------------------


@bp.post("/orders/<int:order_id>/return")
@require_roles("procurement", "inventory", "admin")
def return_goods(order_id: int):
    """Record goods returns for a previously received order."""

    organization_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    lines_payload = payload.get("lines") or []

    if not lines_payload:
        return jsonify({"error": "lines payload is required"}), HTTPStatus.BAD_REQUEST

    po = (
        PurchaseOrder.query.filter_by(organization_id=organization_id, id=order_id)
        .with_for_update()
        .options(joinedload(PurchaseOrder.lines))
        .first_or_404()
    )

    if po.status not in {"partially_received", "received"}:
        return (
            jsonify({"error": f"cannot return goods in status {po.status}"}),
            HTTPStatus.BAD_REQUEST,
        )

    lines_by_id = {line.id: line for line in po.lines}

    try:
        for raw in lines_payload:
            line_id = raw.get("line_id")
            quantity = _parse_decimal(raw.get("quantity"), default="0")
            if not line_id or quantity <= 0:
                raise ValueError("line_id and positive quantity are required")

            line = lines_by_id.get(int(line_id))
            if line is None:
                raise ValueError(f"invalid line_id {line_id}")

            line.return_goods(quantity)
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

    db.session.commit()
    return jsonify(_serialize_order(po))


# ---------------------------------------------------------------------------
# Bulk import / export
# ---------------------------------------------------------------------------


@bp.post("/orders/bulk-import")
@require_roles("procurement", "admin")
def bulk_import_orders():
    """Create multiple purchase orders in one request."""

    organization_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    orders_payload = payload.get("orders") or []

    if not orders_payload:
        return jsonify({"error": "orders array is required"}), HTTPStatus.BAD_REQUEST

    created_ids: list[int] = []

    for po_raw in orders_payload:
        supplier_id = po_raw.get("supplier_id")
        supplier_name = (po_raw.get("supplier_name") or "").strip()
        currency = (po_raw.get("currency") or "ETB").upper()
        lines_payload = po_raw.get("lines") or []

        if not lines_payload:
            db.session.rollback()
            return (
                jsonify({"error": "each order must have at least one line"}),
                HTTPStatus.BAD_REQUEST,
            )

        po = PurchaseOrder(
            organization_id=organization_id,
            supplier_id=supplier_id,
            supplier_name=supplier_name or None,
            currency=currency,
            status="draft",
            created_by_id=getattr(current_user, "id", None),
        )

        for raw in lines_payload:
            item_code = (raw.get("item_code") or "").strip()
            if not item_code:
                db.session.rollback()
                return jsonify({"error": "item_code is required for each line"}), HTTPStatus.BAD_REQUEST

            ordered_quantity = _parse_decimal(raw.get("ordered_quantity"), default="0")
            if ordered_quantity <= 0:
                db.session.rollback()
                return jsonify({"error": "ordered_quantity must be > 0"}), HTTPStatus.BAD_REQUEST

            line = PurchaseOrderLine(
                organization_id=organization_id,
                item_code=item_code,
                item_description=(raw.get("item_description") or "").strip() or None,
                ordered_quantity=ordered_quantity,
                unit_price=_parse_decimal(raw.get("unit_price"), default="0"),
                tax_rate=_parse_decimal(raw.get("tax_rate"), default="0"),
            )
            po.lines.append(line)

        po.recalc_totals()
        db.session.add(po)
        db.session.flush()
        created_ids.append(po.id)

    db.session.commit()
    return jsonify({"created_ids": created_ids}), HTTPStatus.CREATED


@bp.get("/orders/export")
@require_roles("procurement", "inventory", "admin")
def export_orders():
    """Export the latest purchase orders as JSON payload."""

    organization_id = resolve_org_id()
    query = (
        PurchaseOrder.query.filter_by(organization_id=organization_id)
        .options(joinedload(PurchaseOrder.lines))
        .order_by(PurchaseOrder.created_at.desc())
        .limit(1000)
    )
    payload = [_serialize_order(po) for po in query.all()]
    return jsonify({"orders": payload})
