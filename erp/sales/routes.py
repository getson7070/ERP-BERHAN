"""Sales module routes coordinating CRM opportunities and orders."""
from __future__ import annotations

from decimal import Decimal
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_login import login_required

from erp.audit import log_audit
from erp.extensions import db
from erp.models import Inventory, InventoryReservation, SalesOpportunity
from erp.utils import resolve_org_id

from .models import SalesOrder

bp = Blueprint("sales", __name__, url_prefix="/sales")


def _serialize(order: SalesOrder) -> dict[str, object]:
    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "status": order.status,
        "posting_date": order.posting_date.isoformat(),
        "total_value": float(order.total_value),
        "order_id": order.order_id,
    }


@bp.get("/health")
@login_required
def health():
    org_id = resolve_org_id()
    return jsonify({"ok": True, "sales_orders": SalesOrder.query.filter_by(org_id=org_id).count()})


@bp.route("/orders", methods=["GET", "POST"])
@login_required
def manage_orders():
    org_id = resolve_org_id()
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        customer = (payload.get("customer_name") or "").strip()
        if not customer:
            return jsonify({"error": "customer_name is required"}), HTTPStatus.BAD_REQUEST

        total_value = Decimal(str(payload.get("total_value", "0")))
        quantity = int(payload.get("quantity", 0))
        inventory_item_id = payload.get("inventory_item_id")
        sales_order = SalesOrder(
            org_id=org_id,
            customer_name=customer,
            total_value=total_value,
            status=payload.get("status", "submitted").lower(),
            order_id=payload.get("order_id"),
        )
        db.session.add(sales_order)

        if inventory_item_id:
            inventory_item = Inventory.tenant_query(org_id).filter_by(id=inventory_item_id).first()
            if inventory_item is None:
                return jsonify({"error": "inventory_item_id invalid for tenant"}), HTTPStatus.BAD_REQUEST
            if quantity <= 0:
                return jsonify({"error": "quantity must be positive"}), HTTPStatus.BAD_REQUEST

            existing_reservation = InventoryReservation.query.filter_by(
                org_id=org_id, order_id=sales_order.id, inventory_item_id=inventory_item.id
            ).first()
            if existing_reservation is None:
                reservation = InventoryReservation(
                    org_id=org_id,
                    order_id=sales_order.id,
                    inventory_item_id=inventory_item.id,
                    quantity=quantity,
                )
                db.session.add(reservation)
            else:
                existing_reservation.quantity = quantity

            inventory_item.quantity = max(0, inventory_item.quantity - quantity)

        opportunity_id = payload.get("opportunity_id")
        if opportunity_id:
            opportunity = SalesOpportunity.query.filter_by(
                id=opportunity_id, org_id=org_id
            ).first()
            if opportunity is not None:
                opportunity.stage = "won"
                opportunity.order_id = payload.get("order_id")

        db.session.commit()
        log_audit(
            None,
            org_id,
            "sales.order_created",
            f"customer={customer};order={sales_order.id};inventory={inventory_item_id};qty={quantity}",
        )
        return jsonify(_serialize(sales_order)), HTTPStatus.CREATED

    orders = (
        SalesOrder.query.filter_by(org_id=org_id)
        .order_by(SalesOrder.created_at.desc())
        .all()
    )
    return jsonify([_serialize(order) for order in orders])



