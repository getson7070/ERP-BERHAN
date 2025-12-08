"""Procurement workflows: purchase orders, approvals, receipts, and returns."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from http import HTTPStatus
from typing import Any, Iterable, Optional

from flask import Blueprint, jsonify, request
from flask_login import current_user
from sqlalchemy.orm import joinedload

from erp.extensions import db
from erp.models import (
    Inventory,
    ProcurementMilestone,
    ProcurementTicket,
    PurchaseOrder,
    PurchaseOrderLine,
)
from erp.security import require_roles
from erp.utils import resolve_org_id
from erp.utils.activity import log_activity_event

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
        "ticket_id": order.ticket.id if order.ticket else None,
        "lines": [_serialize_line(line) for line in order.lines],
    }


def _parse_decimal(value: Any, default: str = "0") -> Decimal:
    if value is None or value == "":
        return Decimal(default)
    return Decimal(str(value))


def _parse_ts(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        cleaned = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(cleaned)
        except ValueError:
            return None
    return None


def _parse_geo(payload: dict[str, Any]) -> tuple[Optional[float], Optional[float], Optional[float]]:
    lat_raw = payload.get("geo_lat")
    lng_raw = payload.get("geo_lng")
    accuracy_raw = payload.get("geo_accuracy_m")

    lat = float(lat_raw) if lat_raw not in (None, "") else None
    lng = float(lng_raw) if lng_raw not in (None, "") else None
    accuracy = float(accuracy_raw) if accuracy_raw not in (None, "") else None

    if lat is not None and (lat < -90 or lat > 90):
        raise ValueError("geo_lat must be between -90 and 90")
    if lng is not None and (lng < -180 or lng > 180):
        raise ValueError("geo_lng must be between -180 and 180")
    if accuracy is not None and accuracy < 0:
        raise ValueError("geo_accuracy_m must be zero or positive")

    return lat, lng, accuracy


def _serialize_milestone(m: ProcurementMilestone) -> dict[str, Any]:
    return {
        "id": m.id,
        "name": m.name,
        "status": m.status,
        "expected_at": m.expected_at.isoformat() if m.expected_at else None,
        "completed_at": m.completed_at.isoformat() if m.completed_at else None,
        "notes": m.notes,
        "geo": {
            "lat": m.geo_lat,
            "lng": m.geo_lng,
            "accuracy_m": m.geo_accuracy_m,
            "recorded_at": m.recorded_at.isoformat() if m.recorded_at else None,
            "recorded_by_id": m.recorded_by_id,
        },
    }


def _serialize_ticket(ticket: ProcurementTicket) -> dict[str, Any]:
    ticket.evaluate_breach()
    return {
        "id": ticket.id,
        "organization_id": ticket.organization_id,
        "purchase_order_id": ticket.purchase_order_id,
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "sla_due_at": ticket.sla_due_at.isoformat() if ticket.sla_due_at else None,
        "sla_breached": ticket.sla_breached,
        "breached_at": ticket.breached_at.isoformat() if ticket.breached_at else None,
        "escalation_level": ticket.escalation_level,
        "assigned_to_id": ticket.assigned_to_id,
        "created_at": ticket.created_at.isoformat(),
        "created_by_id": ticket.created_by_id,
        "approved_at": ticket.approved_at.isoformat() if ticket.approved_at else None,
        "approved_by_id": ticket.approved_by_id,
        "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
        "closed_reason": ticket.closed_reason,
        "cancelled_at": ticket.cancelled_at.isoformat() if ticket.cancelled_at else None,
        "cancelled_reason": ticket.cancelled_reason,
        "landed_cost_total": float(ticket.landed_cost_total or 0),
        "landed_cost_posted_at": ticket.landed_cost_posted_at.isoformat()
        if ticket.landed_cost_posted_at
        else None,
        "milestones": [_serialize_milestone(m) for m in ticket.milestones],
    }


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

    ticket_id = payload.get("ticket_id")
    if ticket_id:
        ticket = ProcurementTicket.query.filter_by(
            id=int(ticket_id), organization_id=organization_id
        ).first()
        if not ticket:
            return jsonify({"error": "invalid ticket reference"}), HTTPStatus.BAD_REQUEST
        po.ticket = ticket

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

    log_activity_event(
        action="procurement.order_created",
        entity_type="purchase_order",
        entity_id=po.id,
        status=po.status,
        metadata={"currency": po.currency, "line_count": len(lines_payload)},
    )

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
    log_activity_event(
        action="procurement.order_submitted",
        entity_type="purchase_order",
        entity_id=po.id,
        status=po.status,
    )
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
    log_activity_event(
        action="procurement.order_approved",
        entity_type="purchase_order",
        entity_id=po.id,
        status=po.status,
        actor_user_id=po.approved_by_id,
    )
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
    log_activity_event(
        action="procurement.order_cancelled",
        entity_type="purchase_order",
        entity_id=po.id,
        status=po.status,
        metadata={"reason": po.cancel_reason},
    )
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
        _apply_inventory_receipt(organization_id, lines_payload, lines_by_id)
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

    po.update_status_from_lines()
    if po.ticket:
        if po.status in {"received", "partially_received"}:
            po.ticket.mark_status("receiving", getattr(current_user, "id", None))
            po.ticket.evaluate_breach()
    db.session.commit()
    log_activity_event(
        action="procurement.order_received",
        entity_type="purchase_order",
        entity_id=po.id,
        status=po.status,
        metadata={"lines": len(lines_payload)},
    )
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
    log_activity_event(
        action="procurement.order_returned",
        entity_type="purchase_order",
        entity_id=po.id,
        status=po.status,
        metadata={"lines": len(lines_payload)},
    )
    return jsonify(_serialize_order(po))


# ---------------------------------------------------------------------------
# Procurement tickets (imports, SLA, approvals)
# ---------------------------------------------------------------------------


@bp.get("/tickets")
@require_roles("procurement", "inventory", "admin")
def list_tickets() -> Any:
    organization_id = resolve_org_id()
    query = (
        ProcurementTicket.query.filter_by(organization_id=organization_id)
        .options(joinedload(ProcurementTicket.milestones))
        .order_by(ProcurementTicket.created_at.desc())
        .limit(200)
    )
    tickets = query.all()
    for ticket in tickets:
        ticket.evaluate_breach()
    return jsonify([_serialize_ticket(t) for t in tickets])


@bp.post("/tickets")
@require_roles("procurement", "inventory", "admin")
def create_ticket() -> Any:
    organization_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    title = (payload.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), HTTPStatus.BAD_REQUEST

    purchase_order_id = payload.get("purchase_order_id")
    purchase_order = None
    if purchase_order_id:
        purchase_order = PurchaseOrder.query.filter_by(
            id=int(purchase_order_id), organization_id=organization_id
        ).first()
        if not purchase_order:
            return jsonify({"error": "invalid purchase_order_id"}), HTTPStatus.BAD_REQUEST
        if purchase_order.ticket:
            return jsonify({"error": "order already linked to a ticket"}), HTTPStatus.BAD_REQUEST

    ticket = ProcurementTicket(
        organization_id=organization_id,
        purchase_order=purchase_order,
        title=title,
        description=(payload.get("description") or "").strip() or None,
        priority=(payload.get("priority") or "normal").lower(),
        sla_due_at=_parse_ts(payload.get("sla_due_at")),
        assigned_to_id=payload.get("assigned_to_id"),
        status="submitted",
        created_by_id=getattr(current_user, "id", None),
    )

    db.session.add(ticket)
    db.session.commit()
    log_activity_event(
        action="procurement.ticket_created",
        entity_type="procurement_ticket",
        entity_id=ticket.id,
        status=ticket.status,
        metadata={"priority": ticket.priority},
    )
    return jsonify(_serialize_ticket(ticket)), HTTPStatus.CREATED


@bp.get("/tickets/<int:ticket_id>")
@require_roles("procurement", "inventory", "admin")
def ticket_detail(ticket_id: int) -> Any:
    organization_id = resolve_org_id()
    ticket = (
        ProcurementTicket.query.filter_by(organization_id=organization_id, id=ticket_id)
        .options(joinedload(ProcurementTicket.milestones))
        .first_or_404()
    )
    ticket.evaluate_breach()
    db.session.commit()
    return jsonify(_serialize_ticket(ticket))


@bp.post("/tickets/<int:ticket_id>/status")
@require_roles("procurement", "admin")
def update_ticket_status(ticket_id: int) -> Any:
    organization_id = resolve_org_id()
    ticket = (
        ProcurementTicket.query.filter_by(organization_id=organization_id, id=ticket_id)
        .with_for_update()
        .first_or_404()
    )

    payload = request.get_json(silent=True) or {}
    status = (payload.get("status") or "").strip()
    reason = (payload.get("reason") or "").strip() or None

    try:
        ticket.mark_status(status=status, actor_id=getattr(current_user, "id", None), reason=reason)
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

    db.session.commit()
    log_activity_event(
        action="procurement.ticket_status",
        entity_type="procurement_ticket",
        entity_id=ticket.id,
        status=ticket.status,
        metadata={"reason": reason},
    )
    return jsonify(_serialize_ticket(ticket))


@bp.post("/tickets/<int:ticket_id>/milestones")
@require_roles("procurement", "inventory", "admin")
def add_milestone(ticket_id: int) -> Any:
    organization_id = resolve_org_id()
    ticket = (
        ProcurementTicket.query.filter_by(organization_id=organization_id, id=ticket_id)
        .with_for_update()
        .options(joinedload(ProcurementTicket.milestones))
        .first_or_404()
    )

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), HTTPStatus.BAD_REQUEST

    try:
        geo_lat, geo_lng, geo_accuracy_m = _parse_geo(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

    status = (payload.get("status") or "pending").strip() or "pending"
    if status == "completed" and (geo_lat is None or geo_lng is None):
        return (
            jsonify({"error": "geo_lat and geo_lng are required when completing a milestone"}),
            HTTPStatus.BAD_REQUEST,
        )

    milestone = ProcurementMilestone(
        organization_id=organization_id,
        ticket=ticket,
        name=name,
        status=status,
        expected_at=_parse_ts(payload.get("expected_at")),
        completed_at=_parse_ts(payload.get("completed_at")),
        notes=(payload.get("notes") or "").strip() or None,
        geo_lat=geo_lat,
        geo_lng=geo_lng,
        geo_accuracy_m=geo_accuracy_m,
        recorded_by_id=getattr(current_user, "id", None),
    )

    if milestone.status == "completed" and not milestone.completed_at:
        milestone.completed_at = datetime.now(UTC)

    ticket.evaluate_breach()
    db.session.add(milestone)
    db.session.commit()
    log_activity_event(
        action="procurement.milestone_added",
        entity_type="procurement_ticket",
        entity_id=ticket.id,
        status=ticket.status,
        metadata={"milestone": milestone.name, "status": milestone.status},
    )

    return jsonify(_serialize_ticket(ticket)), HTTPStatus.CREATED


@bp.post("/tickets/<int:ticket_id>/landed-cost")
@require_roles("procurement", "admin")
def post_landed_cost(ticket_id: int) -> Any:
    organization_id = resolve_org_id()
    ticket = (
        ProcurementTicket.query.filter_by(organization_id=organization_id, id=ticket_id)
        .with_for_update()
        .first_or_404()
    )

    payload = request.get_json(silent=True) or {}
    amount = _parse_decimal(payload.get("amount"), default="0")
    if amount < 0:
        return jsonify({"error": "amount must be zero or positive"}), HTTPStatus.BAD_REQUEST

    ticket.landed_cost_total = amount
    ticket.landed_cost_posted_at = datetime.now(UTC)
    ticket.mark_status("landed", getattr(current_user, "id", None))

    db.session.commit()
    log_activity_event(
        action="procurement.landed_cost_posted",
        entity_type="procurement_ticket",
        entity_id=ticket.id,
        status=ticket.status,
        metadata={"amount": float(amount)},
    )
    return jsonify(_serialize_ticket(ticket))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _apply_inventory_receipt(
    organization_id: int,
    lines_payload: Iterable[dict[str, Any]],
    lines_by_id: dict[int, PurchaseOrderLine],
) -> None:
    for raw in lines_payload:
        line_id = int(raw.get("line_id"))
        quantity = _parse_decimal(raw.get("quantity"), default="0")
        line = lines_by_id[line_id]
        sku = line.item_code
        item = Inventory.query.filter_by(org_id=organization_id, sku=sku).first()
        if not item:
            item = Inventory(
                org_id=organization_id,
                name=line.item_description or sku,
                sku=sku,
                price=line.unit_price or Decimal("0"),
            )
            db.session.add(item)

        incoming_qty = int(quantity.to_integral_value(rounding=ROUND_HALF_UP))
        item.quantity = (item.quantity or 0) + incoming_qty


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
    log_activity_event(
        action="procurement.bulk_import",
        entity_type="purchase_order",
        entity_id=created_ids[-1] if created_ids else None,
        status="draft",
        metadata={"created_count": len(created_ids)},
    )
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
