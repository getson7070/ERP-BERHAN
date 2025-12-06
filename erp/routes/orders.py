"""Order management endpoints with inventory integration."""
from __future__ import annotations

from decimal import Decimal
from http import HTTPStatus

from flask import Blueprint, jsonify, request

from erp.security import require_roles

from erp.extensions import db
from erp.models import Inventory, InventoryReservation, Order
from erp.utils import resolve_org_id

bp = Blueprint("orders", __name__, url_prefix="/orders")


def _serialize(order: Order) -> dict[str, object]:
    return {
        "id": order.id,
        "status": order.status,
        "currency": order.currency,
        "total_amount": float(order.total_amount),
        "organization_id": order.organization_id,
        "user_id": order.user_id,
        "placed_at": order.placed_at.isoformat(),
    }


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

        order = Order(
            organization_id=org_id,
            user_id=payload.get("user_id"),
            currency=payload.get("currency", "USD"),
            total_amount=total,
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
    valid_statuses = {
        "pending",
        "approved",
        "shipped",
        "canceled",
        "rejected",
        "fulfilled",
    }
    if status not in valid_statuses:
        return (
            jsonify(
                {"error": f"status must be one of {sorted(valid_statuses)}"}
            ),
            HTTPStatus.BAD_REQUEST,
        )

    order.status = status
    db.session.commit()
    return jsonify(_serialize(order))
