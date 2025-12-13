"""Order management endpoints with inventory integration and geo capture."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.extensions import db
from erp.models import Inventory, InventoryReservation, Order
from erp.security_decorators_phase2 import require_permission
from erp.security_rbac_phase2 import ensure_default_policy, is_allowed
from erp.utils import resolve_org_id

bp = Blueprint("orders", __name__, url_prefix="/orders")


def _safe_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _safe_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    if value is None:
        return default
    try:
        return Decimal(str(value).strip())
    except Exception:
        return default


def _extract_geo(payload: dict) -> tuple[float | None, float | None, float | None, str | None]:
    lat_raw = payload.get("geo_lat")
    lng_raw = payload.get("geo_lng")
    acc_raw = payload.get("geo_accuracy_m")

    if lat_raw is None or lng_raw is None:
        return None, None, None, None

    try:
        lat = float(lat_raw)
        lng = float(lng_raw)
    except (TypeError, ValueError):
        return None, None, None, "geo_lat and geo_lng must be numeric"

    if lat < -90 or lat > 90:
        return lat, lng, None, "geo_lat must be between -90 and 90"
    if lng < -180 or lng > 180:
        return lat, lng, None, "geo_lng must be between -180 and 180"

    accuracy = None
    if acc_raw is not None:
        try:
            accuracy = float(acc_raw)
        except (TypeError, ValueError):
            return lat, lng, None, "geo_accuracy_m must be numeric when provided"
        if accuracy < 0:
            return lat, lng, None, "geo_accuracy_m cannot be negative"

    return lat, lng, accuracy, None


def _serialize(order: Order) -> dict[str, Any]:
    return {
        "id": order.id,
        "organization_id": getattr(order, "organization_id", None),
        "status": order.status,
        "payment_status": getattr(order, "payment_status", None),
        "total_amount": str(getattr(order, "total_amount", "0")),
        "initiator_type": getattr(order, "initiator_type", None),
        "initiator_id": getattr(order, "initiator_id", None),
        "assigned_sales_rep_id": getattr(order, "assigned_sales_rep_id", None),
        "commission_enabled": bool(getattr(order, "commission_enabled", False)),
        "commission_rate": str(getattr(order, "commission_rate", "0.02")),
        "commission_status": getattr(order, "commission_status", None),
        "commission_approved_by_management": bool(getattr(order, "commission_approved_by_management", False)),
        "commission_block_reason": getattr(order, "commission_block_reason", None),
        "geo_lat": getattr(order, "geo_lat", None),
        "geo_lng": getattr(order, "geo_lng", None),
        "geo_accuracy_m": getattr(order, "geo_accuracy_m", None),
        "created_at": order.created_at.isoformat() if getattr(order, "created_at", None) else None,
        "updated_at": order.updated_at.isoformat() if getattr(order, "updated_at", None) else None,
    }


@bp.route("/", methods=["GET", "POST"])
@require_permission("orders", "view")
def index():
    org_id = resolve_org_id()

    if request.method == "POST":
        # Enforce create permission explicitly
        ensure_default_policy(int(org_id))
        roles = getattr(current_user, "roles", None) or []
        if not is_allowed(int(org_id), roles, "orders", "create", {"actor_id": getattr(current_user, "id", None)}):
            return (
                jsonify({"error": "permission_denied", "resource": "orders", "action": "create"}),
                HTTPStatus.FORBIDDEN,
            )

        payload = request.get_json(silent=True) or {}
        items = payload.get("items", [])
        if not items:
            return jsonify({"error": "items are required"}), HTTPStatus.BAD_REQUEST

        lat, lng, accuracy, geo_error = _extract_geo(payload)
        if geo_error:
            return jsonify({"error": geo_error}), HTTPStatus.BAD_REQUEST

        initiator_type = (payload.get("initiator_type") or "employee").strip().lower()
        initiator_id = payload.get("initiator_id")
        assigned_sales_rep_id = payload.get("assigned_sales_rep_id")
        commission_enabled = bool(payload.get("commission_enabled", False))
        commission_rate = _safe_decimal(payload.get("commission_rate"), Decimal("0.02"))
        commission_approved = bool(payload.get("commission_approved_by_management", False))
        note = (payload.get("note") or "").strip() or None

        # If client initiated, commission requires management approval
        if initiator_type == "client" and commission_enabled and not commission_approved:
            return (
                jsonify({"error": "commission requires management approval for client-initiated orders"}),
                HTTPStatus.BAD_REQUEST,
            )

        total = Decimal("0")
        reservations: list[InventoryReservation] = []

        for item in items:
            inventory_item_id = item.get("inventory_item_id")
            qty = _safe_int(item.get("quantity"), 0)
            unit_price = _safe_decimal(item.get("unit_price"), Decimal("0"))
            if not inventory_item_id or qty <= 0:
                return jsonify({"error": "inventory_item_id and positive quantity required"}), HTTPStatus.BAD_REQUEST

            inv = Inventory.query.filter_by(org_id=org_id, id=inventory_item_id).first()
            if inv is None:
                return jsonify({"error": f"inventory item {inventory_item_id} not found"}), HTTPStatus.NOT_FOUND

            if inv.quantity < qty:
                return jsonify({"error": f"insufficient stock for item {inventory_item_id}"}), HTTPStatus.CONFLICT

            total += unit_price * Decimal(qty)

            reservations.append(
                InventoryReservation(
                    org_id=org_id,
                    order_id=0,  # filled after order flush
                    inventory_item_id=inv.id,
                    quantity=qty,
                )
            )

        order = Order(
            organization_id=org_id,
            status="submitted",
            payment_status="unpaid",
            total_amount=total,
            note=note,
            initiator_type=initiator_type,
            initiator_id=initiator_id,
            assigned_sales_rep_id=assigned_sales_rep_id,
            commission_enabled=commission_enabled,
            commission_rate=commission_rate,
            commission_approved_by_management=commission_approved,
        )

        if lat is not None and lng is not None:
            order.geo_lat = lat
            order.geo_lng = lng
            order.geo_accuracy_m = accuracy
            order.geo_recorded_by_id = getattr(current_user, "id", None)
            order.geo_recorded_at = datetime.now(UTC)

        # Ensure commission status sync uses model’s own logic if present
        if hasattr(order, "_sync_commission_status"):
            order._sync_commission_status()

        db.session.add(order)
        db.session.flush()

        for r in reservations:
            r.order_id = order.id
            db.session.add(r)

        db.session.commit()
        return jsonify(_serialize(order)), HTTPStatus.CREATED

    orders = (
        Order.query.filter_by(organization_id=org_id)
        .order_by(Order.id.desc())
        .limit(200)
        .all()
    )
    return jsonify([_serialize(order) for order in orders]), HTTPStatus.OK


@bp.patch("/<int:order_id>")
@require_permission("orders", "update")
def update(order_id: int):
    """Update order status and payment state."""
    payload = request.get_json(silent=True) or {}
    status = (payload.get("status") or "").strip().lower()
    payment_status = (payload.get("payment_status") or "").strip().lower()
    note = payload.get("note")

    org_id = resolve_org_id()
    order = Order.query.filter_by(id=order_id, organization_id=org_id).first_or_404()

    if status:
        valid_statuses = set(Order.valid_statuses()) if hasattr(Order, "valid_statuses") else set()
        if valid_statuses and status not in valid_statuses:
            return jsonify({"error": "invalid status"}), HTTPStatus.BAD_REQUEST
        if hasattr(order, "set_status"):
            order.set_status(status)
        else:
            order.status = status

    if payment_status:
        if payment_status not in {"unpaid", "partial", "settled"}:
            return jsonify({"error": "invalid payment_status"}), HTTPStatus.BAD_REQUEST
        if hasattr(order, "set_payment_status"):
            order.set_payment_status(payment_status)
        else:
            order.payment_status = payment_status

    if note is not None:
        order.note = str(note).strip() or None

    lat, lng, accuracy, geo_error = _extract_geo(payload)
    if geo_error:
        return jsonify({"error": geo_error}), HTTPStatus.BAD_REQUEST
    if lat is not None and lng is not None:
        order.geo_lat = lat
        order.geo_lng = lng
        order.geo_accuracy_m = accuracy
        order.geo_recorded_by_id = getattr(current_user, "id", None)
        order.geo_recorded_at = datetime.now(UTC)

    db.session.commit()
    return jsonify(_serialize(order)), HTTPStatus.OK
