"""Inventory extensions: warehouses, cycle counts, reorder rules, and safe adjustments."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.extensions import db
from erp.inventory.models import (
    CycleCount,
    CycleCountLine,
    InventoryLocation,
    Lot,
    ReorderRule,
    StockBalance,
    Warehouse,
)
from erp.security import require_roles
from erp.services.stock_service import adjust_stock
from erp.utils import resolve_org_id

bp = Blueprint("inventory_ext_api", __name__, url_prefix="/api/inventory")


def _parse_decimal(value: Any, default: str = "0") -> Decimal:
    if value is None or value == "":
        return Decimal(default)
    return Decimal(str(value))


# ---------------------------------------------------------------------------
# Warehouses and locations
# ---------------------------------------------------------------------------


def _serialize_warehouse(w: Warehouse) -> dict[str, Any]:
    return {
        "id": str(w.id),
        "code": w.code,
        "name": w.name,
        "address": w.address,
        "region": w.region,
        "is_default": w.is_default,
        "is_active": w.is_active,
    }


def _serialize_location(loc: InventoryLocation) -> dict[str, Any]:
    return {
        "id": str(loc.id),
        "warehouse_id": str(loc.warehouse_id),
        "code": loc.code,
        "name": loc.name,
        "is_active": loc.is_active,
    }


@bp.post("/warehouses")
@require_roles("inventory", "admin")
def create_warehouse():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    code = (payload.get("code") or "").upper().strip()
    name = (payload.get("name") or "").strip()
    if not (code and name):
        return jsonify({"error": "code and name are required"}), HTTPStatus.BAD_REQUEST

    warehouse = Warehouse(
        org_id=org_id,
        code=code,
        name=name,
        address=(payload.get("address") or None),
        region=(payload.get("region") or None),
        is_default=bool(payload.get("is_default", False)),
        is_active=True,
        created_at=datetime.now(UTC),
    )
    db.session.add(warehouse)
    db.session.commit()
    return jsonify(_serialize_warehouse(warehouse)), HTTPStatus.CREATED


@bp.get("/warehouses")
@require_roles("inventory", "admin")
def list_warehouses():
    org_id = resolve_org_id()
    rows = Warehouse.query.filter_by(org_id=org_id, is_active=True).order_by(Warehouse.name.asc()).all()
    return jsonify([_serialize_warehouse(w) for w in rows]), HTTPStatus.OK


@bp.post("/warehouses/<uuid:warehouse_id>/locations")
@require_roles("inventory", "admin")
def create_location(warehouse_id):
    org_id = resolve_org_id()
    warehouse = Warehouse.query.filter_by(org_id=org_id, id=warehouse_id).first_or_404()
    payload = request.get_json(silent=True) or {}
    code = (payload.get("code") or "").upper().strip()
    if not code:
        return jsonify({"error": "code is required"}), HTTPStatus.BAD_REQUEST

    location = InventoryLocation(
        org_id=org_id,
        warehouse_id=warehouse.id,
        code=code,
        name=(payload.get("name") or None),
        is_active=True,
        created_at=datetime.now(UTC),
    )
    db.session.add(location)
    db.session.commit()
    return jsonify(_serialize_location(location)), HTTPStatus.CREATED


# ---------------------------------------------------------------------------
# Lots / expiry
# ---------------------------------------------------------------------------


def _serialize_lot(lot: Lot) -> dict[str, Any]:
    return {
        "id": str(lot.id),
        "item_id": str(lot.item_id),
        "lot_number": lot.number,
        "expiry_date": lot.expiry.isoformat() if lot.expiry else None,
        "manufacture_date": lot.manufacture_date.isoformat() if lot.manufacture_date else None,
        "received_date": lot.received_date.isoformat() if lot.received_date else None,
        "is_active": lot.is_active,
    }


@bp.post("/lots")
@require_roles("inventory", "admin")
def create_lot():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    if not payload.get("item_id"):
        return jsonify({"error": "item_id is required"}), HTTPStatus.BAD_REQUEST

    lot = Lot(
        org_id=org_id,
        item_id=payload["item_id"],
        number=(payload.get("lot_number") or "").strip(),
        expiry=date.fromisoformat(payload["expiry_date"]) if payload.get("expiry_date") else None,
        manufacture_date=date.fromisoformat(payload["manufacture_date"]) if payload.get("manufacture_date") else None,
        received_date=date.fromisoformat(payload["received_date"]) if payload.get("received_date") else None,
        supplier_id=payload.get("supplier_id"),
        is_active=True,
        created_at=datetime.now(UTC),
    )
    db.session.add(lot)
    db.session.commit()
    return jsonify(_serialize_lot(lot)), HTTPStatus.CREATED


@bp.get("/lots/expiring")
@require_roles("inventory", "admin")
def expiring_lots():
    org_id = resolve_org_id()
    days = int(request.args.get("days", "90"))
    cutoff = date.today() + timedelta(days=days)
    lots = (
        Lot.query.filter(
            Lot.org_id == org_id,
            Lot.is_active.is_(True),
            Lot.expiry.isnot(None),
            Lot.expiry <= cutoff,
        )
        .order_by(Lot.expiry.asc())
        .limit(500)
        .all()
    )
    return jsonify([_serialize_lot(l) for l in lots]), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Cycle counts
# ---------------------------------------------------------------------------
@bp.post("/cycle-counts")
@require_roles("inventory", "admin")
def create_cycle_count():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    if not payload.get("warehouse_id"):
        return jsonify({"error": "warehouse_id is required"}), HTTPStatus.BAD_REQUEST

    cc = CycleCount(
        org_id=org_id,
        warehouse_id=payload["warehouse_id"],
        location_id=payload.get("location_id"),
        status="open",
        counted_by_id=getattr(current_user, "id", None),
        created_at=datetime.now(UTC),
    )
    db.session.add(cc)
    db.session.flush()

    for raw in payload.get("lines", []):
        bal = StockBalance.query.filter_by(
            org_id=org_id,
            item_id=raw.get("item_id"),
            warehouse_id=payload["warehouse_id"],
            location_id=raw.get("location_id"),
            lot_id=raw.get("lot_id"),
        ).first()
        system_qty = Decimal(bal.qty_on_hand) if bal else Decimal("0")
        counted_qty = _parse_decimal(raw.get("counted_qty"), default=str(system_qty))
        line = CycleCountLine(
            org_id=org_id,
            cycle_count_id=cc.id,
            item_id=raw.get("item_id"),
            lot_id=raw.get("lot_id"),
            location_id=raw.get("location_id"),
            system_qty=system_qty,
            counted_qty=counted_qty,
            variance=counted_qty - system_qty,
        )
        db.session.add(line)
    db.session.commit()
    return jsonify({"id": str(cc.id), "status": cc.status}), HTTPStatus.CREATED


@bp.post("/cycle-counts/<uuid:cc_id>/submit")
@require_roles("inventory", "admin")
def submit_cycle_count(cc_id):
    org_id = resolve_org_id()
    cc = CycleCount.query.filter_by(org_id=org_id, id=cc_id).first_or_404()
    if cc.status != "open":
        return jsonify({"error": "cycle count not open"}), HTTPStatus.BAD_REQUEST

    cc.status = "submitted"
    cc.submitted_at = datetime.now(UTC)
    db.session.commit()
    return jsonify({"status": cc.status}), HTTPStatus.OK


@bp.post("/cycle-counts/<uuid:cc_id>/approve")
@require_roles("inventory_manager", "admin")
def approve_cycle_count(cc_id):
    org_id = resolve_org_id()
    cc = CycleCount.query.filter_by(org_id=org_id, id=cc_id).first_or_404()
    if cc.status != "submitted":
        return jsonify({"error": "cycle count not submitted"}), HTTPStatus.BAD_REQUEST

    for line in cc.lines:
        if line.variance == 0:
            continue
        adjust_stock(
            org_id=org_id,
            item_id=line.item_id,
            warehouse_id=cc.warehouse_id,
            location_id=line.location_id,
            lot_id=line.lot_id,
            qty_delta=Decimal(line.variance),
            tx_type="cycle_count",
            reference_type="CYCLE_COUNT",
            reference_id=cc.id,
            created_by_id=getattr(current_user, "id", None),
            idempotency_key=f"cc:{cc.id}:line:{line.id}",
        )

    cc.status = "approved"
    cc.approved_at = datetime.now(UTC)
    cc.approved_by_id = getattr(current_user, "id", None)
    db.session.commit()
    return jsonify({"status": cc.status}), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Reorder rules and scan trigger
# ---------------------------------------------------------------------------


def _serialize_reorder_rule(rule: ReorderRule) -> dict[str, Any]:
    return {
        "id": str(rule.id),
        "item_id": str(rule.item_id),
        "warehouse_id": str(rule.warehouse_id),
        "min_qty": float(rule.min_qty or 0),
        "max_qty": float(rule.max_qty or 0),
        "reorder_qty": float(rule.reorder_qty or 0) if rule.reorder_qty is not None else None,
        "lead_time_days": rule.lead_time_days,
        "is_active": rule.is_active,
    }


@bp.post("/reorder-rules")
@require_roles("inventory", "admin")
def upsert_reorder_rule():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    item_id = payload.get("item_id")
    warehouse_id = payload.get("warehouse_id")
    if not (item_id and warehouse_id):
        return jsonify({"error": "item_id and warehouse_id are required"}), HTTPStatus.BAD_REQUEST

    rule = ReorderRule.query.filter_by(org_id=org_id, item_id=item_id, warehouse_id=warehouse_id).first()
    if not rule:
        rule = ReorderRule(org_id=org_id, item_id=item_id, warehouse_id=warehouse_id)
        db.session.add(rule)

    rule.min_qty = _parse_decimal(payload.get("min_qty"))
    rule.max_qty = _parse_decimal(payload.get("max_qty"))
    rule.reorder_qty = _parse_decimal(payload.get("reorder_qty")) if payload.get("reorder_qty") else None
    rule.lead_time_days = int(payload.get("lead_time_days", rule.lead_time_days or 7))
    rule.is_active = bool(payload.get("is_active", True))

    db.session.commit()
    return jsonify(_serialize_reorder_rule(rule)), HTTPStatus.OK


@bp.post("/adjust")
@require_roles("inventory", "admin")
def adjust_inventory():
    """Manual adjustment endpoint used by stress tests and admin tools."""
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    try:
        ledger = adjust_stock(
            org_id=org_id,
            item_id=payload["item_id"],
            warehouse_id=payload["warehouse_id"],
            location_id=payload.get("location_id"),
            lot_id=payload.get("lot_id"),
            qty_delta=_parse_decimal(payload.get("qty_delta")),
            tx_type=payload.get("tx_type", "adjust"),
            reference_type=payload.get("reference_type"),
            reference_id=payload.get("reference_id"),
            idempotency_key=payload.get("idempotency_key"),
            unit_cost=_parse_decimal(payload.get("unit_cost")),
            created_by_id=getattr(current_user, "id", None),
        )
        db.session.commit()
    except (KeyError, ValueError) as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

    return jsonify({"ledger_id": str(ledger.id)}), HTTPStatus.CREATED


@bp.post("/reorder-scan")
@require_roles("inventory", "admin")
def trigger_reorder_scan():
    """Invoke the background reorder scan task."""
    from erp.celery_app import celery_app

    if hasattr(celery_app, "send_task"):
        celery_app.send_task("erp.tasks.inventory.reorder_scan")
    else:
        celery_app.send_task("erp.tasks.inventory.reorder_scan")  # type: ignore[call-arg]
    return jsonify({"status": "scheduled"}), HTTPStatus.ACCEPTED
