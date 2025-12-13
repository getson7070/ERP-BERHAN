"""Order management endpoints with inventory integration and geo audit."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.security_decorators_phase2 import require_permission
from erp.security_rbac_phase2 import ensure_default_policy, is_allowed

from erp.extensions import db
from erp.models import Inventory, InventoryReservation, Order, User
from erp.utils import resolve_org_id
from erp.utils.activity import log_activity_event

bp = Blueprint("orders", __name__, url_prefix="/orders")


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


@bp.route("/", methods=["GET", "POST"])
@require_permission("orders", "view")
def index():
    org_id = resolve_org_id()

    # Policy-based enforcement: POST requires create permission (view is not sufficient).
    if request.method == "POST":
        ensure_default_policy(org_id)
        roles = getattr(current_user, "roles", None) or []
        ctx = {"actor_id": getattr(current_user, "id", None)}
        if not is_allowed(org_id, roles, "orders", "create", ctx):
            return (
                jsonify({"error": "permission_denied", "resource": "orders", "action": "create"}),
                HTTPStatus.FORBIDDEN,
            )

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        items = payload.get("items", [])
        if not items:
            return jsonify({"error": "items are required"}), HTTPStatus.BAD_REQUEST

        initiator_type = (payload.get("initiator_type") or "employee").strip().lower()
        if initiator_type not in {"client", "employee", "management"}:
            return jsonify({"error": "invalid initiator_type"}), HTTPStatus.BAD_REQUEST

        assigned_sales_rep_id = payload.get("assigned_sales_rep_id")
        commission_enabled = bool(payload.get("commission_enabled", False))
        commission_rate = Decimal(str(payload.get("commission_rate", "0.02")))
        commission_approved = bool(payload.get("commission_approved_by_management", False))

        # enforce commission rules:
        # - if client initiates, commission must be explicitly approved by management
        if initiator_type == "client" and commission_enabled and not commission_approved:
            return (
                jsonify({"error": "commission requires management approval for client-initiated orders"}),
                HTTPStatus.BAD_REQUEST,
            )

        note = (payload.get("note") or "").strip()

        lat, lng, accuracy, geo_error = _extract_geo(payload)
        if geo_error:
            return jsonify({"error": geo_error}), HTTPStatus.BAD_REQUEST

        total = Decimal("0")
        reservations: list[InventoryReservation] = []
        for item in items:
            inventory_id = item.get("inventory_item_id")
            quantity = int(item.get("quantity", 0))
            unit_price = Decimal(str(item.get("unit_price", "0")))
            if not inventory_id or quantity <= 0:
                return (
                    jsonify({"error": "inventory_item_id and positive quantity required"}),
                    HTTPStatus.BAD_REQUEST,
                )

            inv = Inventory.query.filter_by(org_id=org_id, id=inventory_id).first()
            if inv is None:
                return jsonify({"error": f"inventory item {inventory_id} not found"}), HTTPStatus.NOT_FOUND

            if inv.quantity_available < quantity:
                return (
                    jsonify({"error": f"insufficient stock for item {inventory_id}"}),
                    HTTPStatus.CONFLICT,
                )

            line_total = unit_price * Decimal(quantity)
            total += line_total

            reservation = InventoryReservation(
                org_id=org_id,
                inventory_item_id=inv.id,
                quantity=quantity,
                reserved_at=datetime.now(UTC),
                reserved_by_id=getattr(current_user, "id", None),
            )
            reservations.append(reservation)

        order = Order(
            org_id=org_id,
            status="pending",
            total_amount=total,
            note=note,
            initiator_type=initiator_type,
            assigned_sales_rep_id=assigned_sales_rep_id,
            commission_enabled=commission_enabled,
            commission_rate=commission_rate,
            commission_approved_by_management=commission_approved,
            created_at=datetime.now(UTC),
            created_by_id=getattr(current_user, "id", None),
        )

        if lat is not None and lng is not None:
            order.geo_lat = lat
            order.geo_lng = lng
            order.geo_accuracy_m = accuracy
            order.geo_recorded_at = datetime.now(UTC)
            order.geo_recorded_by_id = getattr(current_user, "id", None)

        db.session.add(order)
        db.session.flush()

        for reservation in reservations:
            reservation.order_id = order.id
            db.session.add(reservation)

        order.recalculate_commission_status()
        db.session.commit()

        log_activity_event(
            actor_id=getattr(current_user, "id", None),
            org_id=org_id,
            event_type="order_created",
            entity_type="order",
            entity_id=order.id,
            meta={
                "initiator_type": initiator_type,
                "commission_enabled": commission_enabled,
                "assigned_sales_rep_id": assigned_sales_rep_id,
            },
        )

        return jsonify({"ok": True, "order_id": order.id}), HTTPStatus.CREATED

    # GET list
    qs = Order.query.filter_by(org_id=org_id).order_by(Order.id.desc()).limit(200)
    rows = []
    for o in qs.all():
        rows.append(
            {
                "id": o.id,
                "status": o.status,
                "total_amount": str(o.total_amount),
                "initiator_type": o.initiator_type,
                "assigned_sales_rep_id": o.assigned_sales_rep_id,
                "commission_enabled": bool(o.commission_enabled),
                "commission_rate": str(o.commission_rate),
                "commission_status": o.commission_status,
                "payment_status": o.payment_status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
        )
    return jsonify({"orders": rows}), HTTPStatus.OK


@bp.patch("/<int:order_id>")
@require_permission("orders", "update")
def update(order_id: int):
    org_id = resolve_org_id()
    order = Order.query.filter_by(org_id=org_id, id=order_id).first()
    if order is None:
        return jsonify({"error": "order not found"}), HTTPStatus.NOT_FOUND

    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    payment_status = payload.get("payment_status")
    note = payload.get("note")

    if status is not None:
        order.status = str(status).strip()

    if payment_status is not None:
        payment_status = str(payment_status).strip().lower()
        if payment_status not in {"unpaid", "partial", "settled"}:
            return jsonify({"error": "invalid payment_status"}), HTTPStatus.BAD_REQUEST
        order.set_payment_status(payment_status)

    if note is not None:
        order.note = str(note).strip()

    lat, lng, accuracy, geo_error = _extract_geo(payload)
    if geo_error:
        return jsonify({"error": geo_error}), HTTPStatus.BAD_REQUEST

    if lat is not None and lng is not None:
        order.geo_lat = lat
        order.geo_lng = lng
        order.geo_accuracy_m = accuracy
        order.geo_recorded_at = datetime.now(UTC)
        order.geo_recorded_by_id = getattr(current_user, "id", None)

    order.recalculate_commission_status()
    db.session.commit()

    log_activity_event(
        actor_id=getattr(current_user, "id", None),
        org_id=org_id,
        event_type="order_updated",
        entity_type="order",
        entity_id=order.id,
        meta={"status": order.status, "payment_status": order.payment_status},
    )

    return jsonify({"ok": True}), HTTPStatus.OK
