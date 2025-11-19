"""Supply chain orchestration blueprint."""
from __future__ import annotations

from datetime import date
from http import HTTPStatus
import uuid

from flask import Blueprint, jsonify, request

from erp.security import require_roles
from erp.utils import resolve_org_id
from erp.extensions import db
from erp.models import Inventory, InventoryReservation, SupplyChainShipment

from .models import ReorderPolicy

supply_bp = Blueprint("supplychain", __name__, url_prefix="/supply")
bp = supply_bp


def _serialize_policy(policy: ReorderPolicy) -> dict[str, object]:
    return {
        "id": policy.id,
        "item_id": str(policy.item_id),
        "warehouse_id": str(policy.warehouse_id),
        "service_level": float(policy.service_level or 0),
        "safety_stock": float(policy.safety_stock or 0),
        "reorder_point": float(policy.reorder_point or 0),
    }


@supply_bp.route("/policy", methods=["GET", "POST"])
@require_roles("supply_chain", "manager", "admin")
def policy():
    """Manage dynamic reorder policies for inventory items."""

    org_id = resolve_org_id()
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        item_id = data.get("item_id")
        warehouse_id = data.get("warehouse_id")
        if not item_id or not warehouse_id:
            return (
                jsonify({"error": "item_id and warehouse_id are required"}),
                HTTPStatus.BAD_REQUEST,
            )
        try:
            parsed_item_id = uuid.UUID(str(item_id))
            parsed_warehouse_id = uuid.UUID(str(warehouse_id))
        except (TypeError, ValueError):
            return (
                jsonify(
                    {"error": "item_id and warehouse_id must be valid UUIDs"}
                ),
                HTTPStatus.BAD_REQUEST,
            )

        policy = ReorderPolicy(
            org_id=org_id,
            item_id=str(parsed_item_id),
            warehouse_id=str(parsed_warehouse_id),
            service_level=data.get("service_level", 0.95),
            safety_stock=data.get("safety_stock", 0),
            reorder_point=data.get("reorder_point", 0),
        )
        db.session.add(policy)
        db.session.commit()
        return jsonify(_serialize_policy(policy)), HTTPStatus.CREATED

    rows = ReorderPolicy.query.filter_by(org_id=org_id).all()
    return jsonify([_serialize_policy(row) for row in rows])


@supply_bp.route("/shipments", methods=["GET", "POST"])
@require_roles("supply_chain", "manager", "admin")
def shipments():
    """Create shipments that fulfil orders and update reservations."""

    org_id = resolve_org_id()
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        vendor = (data.get("vendor_name") or "").strip()
        order_id = data.get("order_id")
        if not vendor or not order_id:
            return (
                jsonify({"error": "vendor_name and order_id required"}),
                HTTPStatus.BAD_REQUEST,
            )

        shipment = SupplyChainShipment(
            org_id=org_id,
            vendor_name=vendor,
            order_id=order_id,
            status=data.get("status", "in_transit"),
            expected_date=data.get("expected_date", date.today()),
        )
        db.session.add(shipment)

        if data.get("release_inventory"):
            reservations = InventoryReservation.query.filter_by(
                org_id=org_id, order_id=order_id
            ).all()
            for reservation in reservations:
                inventory = Inventory.query.get(reservation.inventory_item_id)
                if inventory is not None:
                    inventory.quantity += reservation.quantity
                db.session.delete(reservation)

        db.session.commit()
        return (
            jsonify(
                {
                    "id": shipment.id,
                    "status": shipment.status,
                }
            ),
            HTTPStatus.CREATED,
        )

    shipments = (
        SupplyChainShipment.query.filter_by(org_id=org_id)
        .order_by(SupplyChainShipment.created_at.desc())
        .all()
    )
    payload = [
        {
            "id": shipment.id,
            "vendor_name": shipment.vendor_name,
            "order_id": shipment.order_id,
            "status": shipment.status,
            "expected_date": shipment.expected_date.isoformat()
            if shipment.expected_date
            else None,
            "received_date": shipment.received_date.isoformat()
            if shipment.received_date
            else None,
        }
        for shipment in shipments
    ]
    return jsonify(payload)


__all__ = ["bp", "policy", "shipments"]
