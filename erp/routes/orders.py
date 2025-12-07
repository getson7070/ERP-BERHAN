"""Order management endpoints with inventory integration."""
from __future__ import annotations

from decimal import Decimal
from http import HTTPStatus

from flask import Blueprint, jsonify, request

from erp.security import require_roles

from erp.extensions import db
from erp.models import Inventory, InventoryReservation, Order, User
from erp.utils import resolve_org_id

bp = Blueprint("orders", __name__, url_prefix="/orders")


def _serialize(order: Order) -> dict[str, object]:
    return {
        "id": order.id,
        "status": order.status,
        "payment_status": order.payment_status,
        "currency": order.currency,
        "total_amount": float(order.total_amount),
        "organization_id": order.organization_id,
        "user_id": order.user_id,
        "initiator_type": order.initiator_type,
        "initiator_id": order.initiator_id,
        "assigned_sales_rep_id": order.assigned_sales_rep_id,
        "commission_enabled": order.commission_enabled,
        "commission_rate": float(order.commission_rate or 0),
        "commission_status": order.commission_status,
        "commission_amount": float(order.commission_amount),
        "placed_at": order.placed_at.isoformat() if order.placed_at else None,
    }


def _as_bool(value: object, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


@bp.route("/", methods=["GET", "POST"])
@require_roles("sales", "admin")
def index():
    org_id = resolve_org_id()
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        items = payload.get("items", [])
        if not items:
            return jsonify({"error": "items are required"}), HTTPStatus.BAD_REQUEST

        total = Decimal("0")
        reservations: list[InventoryReservation] = []
        for item in items:
            inventory_id = item.get("inventory_item_id")
            quantity = int(item.get("quantity", 0))
            unit_price = Decimal(str(item.get("unit_price", "0")))
            if not inventory_id or quantity <= 0:
                return (
                    jsonify(
                        {"error": "inventory_item_id and positive quantity required"}
                    ),
                    HTTPStatus.BAD_REQUEST,
                )

            inventory = Inventory.query.filter_by(id=inventory_id, org_id=org_id).first()
            if inventory is None:
                return (
                    jsonify({"error": f"inventory item {inventory_id} not found"}),
                    HTTPStatus.BAD_REQUEST,
                )
            if inventory.quantity < quantity:
                return (
                    jsonify(
                        {"error": f"insufficient stock for {inventory.sku}"}
                    ),
                    HTTPStatus.CONFLICT,
                )

            total += unit_price * quantity
            reservations.append(
                InventoryReservation(
                    org_id=org_id,
                    inventory_item_id=inventory.id,
                    quantity=quantity,
                )
            )
            inventory.quantity -= quantity

        initiator_type = (payload.get("initiator_type") or "").lower() or None
        if initiator_type and initiator_type not in {"client", "employee", "management"}:
            return (
                jsonify({"error": "initiator_type must be client, employee, or management"}),
                HTTPStatus.BAD_REQUEST,
            )

        assigned_sales_rep_id = payload.get("assigned_sales_rep_id")
        if assigned_sales_rep_id is not None:
            rep = User.query.filter_by(id=assigned_sales_rep_id).first()
            if rep is None:
                return (
                    jsonify({"error": "assigned_sales_rep_id is invalid"}),
                    HTTPStatus.BAD_REQUEST,
                )

        commission_enabled = _as_bool(payload.get("commission_enabled"), default=False)
        commission_rate = payload.get("commission_rate")
        try:
            commission_rate_decimal = (
                Decimal(str(commission_rate)) if commission_rate is not None else Decimal("0.02")
            )
        except Exception:
            return (
                jsonify({"error": "commission_rate must be numeric"}),
                HTTPStatus.BAD_REQUEST,
            )

        order = Order(
            organization_id=org_id,
            user_id=payload.get("user_id"),
            currency=payload.get("currency", "USD"),
            total_amount=total,
            initiator_type=initiator_type,
            initiator_id=payload.get("initiator_id"),
            assigned_sales_rep_id=assigned_sales_rep_id,
            commission_enabled=commission_enabled,
            commission_rate=commission_rate_decimal,
            status="submitted",
            payment_status="unpaid",
            commission_status="pending" if commission_enabled else "none",
        )
        db.session.add(order)
        db.session.flush()

        for reservation in reservations:
            reservation.order_id = order.id
            db.session.add(reservation)

        db.session.commit()
        return jsonify(_serialize(order)), HTTPStatus.CREATED

    orders = (
        Order.query.filter_by(organization_id=org_id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return jsonify([_serialize(order) for order in orders])


@bp.patch("/<int:order_id>")
@require_roles("sales", "admin")
def update(order_id: int):
    """Update order status (approve, cancel, fulfil)."""

    payload = request.get_json(silent=True) or {}
    status = (payload.get("status") or "").lower()
    org_id = resolve_org_id()
    order = Order.query.filter_by(id=order_id, organization_id=org_id).first_or_404()
    if status:
        valid_statuses = set(Order.valid_statuses())
        if status not in valid_statuses:
            return (
                jsonify({"error": f"status must be one of {sorted(valid_statuses)}"}),
                HTTPStatus.BAD_REQUEST,
            )
        order.set_status(status)

    if "payment_status" in payload:
        payment_status = (payload.get("payment_status") or "").lower()
        valid_payment_statuses = {"unpaid", "partial", "settled"}
        if payment_status not in valid_payment_statuses:
            return (
                jsonify({"error": f"payment_status must be one of {sorted(valid_payment_statuses)}"}),
                HTTPStatus.BAD_REQUEST,
            )
        order.set_payment_status(payment_status)

    if "commission_enabled" in payload:
        order.set_commission_enabled(_as_bool(payload.get("commission_enabled")))

    if "commission_rate" in payload:
        commission_rate_val = payload.get("commission_rate")
        try:
            order.commission_rate = Decimal(str(commission_rate_val))
        except Exception:
            return (
                jsonify({"error": "commission_rate must be numeric"}),
                HTTPStatus.BAD_REQUEST,
            )

    if "assigned_sales_rep_id" in payload:
        rep_id = payload.get("assigned_sales_rep_id")
        if rep_id is not None:
            rep = User.query.filter_by(id=rep_id).first()
            if rep is None:
                return (
                    jsonify({"error": "assigned_sales_rep_id is invalid"}),
                    HTTPStatus.BAD_REQUEST,
                )
        order.assigned_sales_rep_id = rep_id

    db.session.commit()
    return jsonify(_serialize(order))
