"""Maintenance API covering assets, schedules, work orders, and KPIs."""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user
from erp.extensions import db
from erp.models import (
    MaintenanceAsset,
    MaintenanceEscalationRule,
    MaintenanceEvent,
    MaintenanceSchedule,
    MaintenanceSensorReading,
    MaintenanceWorkOrder,
)
from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("maintenance_api", __name__, url_prefix="/api/maintenance")


def _parse_decimal(value: Any, default: str = "0") -> Decimal:
    if value is None or value == "":
        return Decimal(default)
    return Decimal(str(value))


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

def _serialize_asset(asset: MaintenanceAsset) -> dict[str, Any]:
    return {
        "id": asset.id,
        "code": asset.code,
        "name": asset.name,
        "category": asset.category,
        "manufacturer": asset.manufacturer,
        "model": asset.model,
        "serial_number": asset.serial_number,
        "location": asset.location,
        "purchase_date": asset.purchase_date.isoformat() if asset.purchase_date else None,
        "purchase_cost": float(asset.purchase_cost or 0),
        "salvage_value": float(asset.salvage_value or 0),
        "useful_life_years": asset.useful_life_years,
        "depreciation_method": asset.depreciation_method,
        "is_critical": asset.is_critical,
        "is_active": asset.is_active,
        "created_at": asset.created_at.isoformat(),
    }


@bp.get("/assets")
@require_roles("maintenance", "admin")
def list_assets():
    org_id = resolve_org_id()
    q = (
        MaintenanceAsset.query.filter_by(org_id=org_id, is_active=True)
        .order_by(MaintenanceAsset.name.asc())
    )
    return jsonify([_serialize_asset(a) for a in q.all()]), HTTPStatus.OK


@bp.post("/assets")
@require_roles("maintenance", "admin")
def create_asset():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    code = (payload.get("code") or "").strip()
    name = (payload.get("name") or "").strip()
    if not (code and name):
        return jsonify({"error": "code and name are required"}), HTTPStatus.BAD_REQUEST

    asset = MaintenanceAsset(
        org_id=org_id,
        code=code,
        name=name,
        category=(payload.get("category") or "").strip() or None,
        manufacturer=(payload.get("manufacturer") or "").strip() or None,
        model=(payload.get("model") or "").strip() or None,
        serial_number=(payload.get("serial_number") or "").strip() or None,
        location=(payload.get("location") or "").strip() or None,
        purchase_date=date.fromisoformat(payload["purchase_date"]) if payload.get("purchase_date") else None,
        purchase_cost=_parse_decimal(payload.get("purchase_cost")),
        salvage_value=_parse_decimal(payload.get("salvage_value")),
        useful_life_years=payload.get("useful_life_years"),
        depreciation_method=(payload.get("depreciation_method") or "straight_line"),
        is_critical=bool(payload.get("is_critical", False)),
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(asset)
    db.session.commit()
    return jsonify(_serialize_asset(asset)), HTTPStatus.CREATED


# ---------------------------------------------------------------------------
# Schedules
# ---------------------------------------------------------------------------

def _serialize_schedule(schedule: MaintenanceSchedule) -> dict[str, Any]:
    return {
        "id": schedule.id,
        "asset_id": schedule.asset_id,
        "name": schedule.name,
        "schedule_type": schedule.schedule_type,
        "interval_days": schedule.interval_days,
        "next_due_date": schedule.next_due_date.isoformat() if schedule.next_due_date else None,
        "last_completed_date": schedule.last_completed_date.isoformat() if schedule.last_completed_date else None,
        "usage_metric": schedule.usage_metric,
        "usage_interval": schedule.usage_interval,
        "is_active": schedule.is_active,
    }


@bp.post("/assets/<int:asset_id>/schedules")
@require_roles("maintenance", "admin")
def create_schedule(asset_id: int):
    org_id = resolve_org_id()
    asset = MaintenanceAsset.query.filter_by(org_id=org_id, id=asset_id).first_or_404()

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), HTTPStatus.BAD_REQUEST

    schedule = MaintenanceSchedule(
        org_id=org_id,
        asset_id=asset.id,
        name=name,
        schedule_type=(payload.get("schedule_type") or "time").lower(),
        interval_days=payload.get("interval_days"),
        next_due_date=date.fromisoformat(payload["next_due_date"]) if payload.get("next_due_date") else None,
        usage_metric=(payload.get("usage_metric") or "").strip() or None,
        usage_interval=payload.get("usage_interval"),
        is_active=True,
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(schedule)
    db.session.commit()
    return jsonify(_serialize_schedule(schedule)), HTTPStatus.CREATED


# ---------------------------------------------------------------------------
# Work orders
# ---------------------------------------------------------------------------

def _serialize_work_order(work_order: MaintenanceWorkOrder) -> dict[str, Any]:
    return {
        "id": work_order.id,
        "asset_id": work_order.asset_id,
        "schedule_id": work_order.schedule_id,
        "work_type": work_order.work_type,
        "title": work_order.title,
        "description": work_order.description,
        "status": work_order.status,
        "priority": work_order.priority,
        "requested_by_id": work_order.requested_by_id,
        "assigned_to_id": work_order.assigned_to_id,
        "requested_at": work_order.requested_at.isoformat(),
        "due_date": work_order.due_date.isoformat() if work_order.due_date else None,
        "started_at": work_order.started_at.isoformat() if work_order.started_at else None,
        "completed_at": work_order.completed_at.isoformat() if work_order.completed_at else None,
        "downtime_start": work_order.downtime_start.isoformat() if work_order.downtime_start else None,
        "downtime_end": work_order.downtime_end.isoformat() if work_order.downtime_end else None,
        "downtime_minutes": work_order.downtime_minutes,
        "labor_cost": float(work_order.labor_cost or 0),
        "material_cost": float(work_order.material_cost or 0),
        "other_cost": float(work_order.other_cost or 0),
        "total_cost": float(work_order.total_cost or 0),
    }


@bp.post("/work-orders")
@require_roles("maintenance", "admin")
def create_work_order():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    title = (payload.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), HTTPStatus.BAD_REQUEST

    work_order = MaintenanceWorkOrder(
        org_id=org_id,
        asset_id=payload.get("asset_id"),
        schedule_id=payload.get("schedule_id"),
        work_type=(payload.get("work_type") or "corrective").lower(),
        title=title,
        description=(payload.get("description") or "").strip() or None,
        status="open",
        priority=(payload.get("priority") or "normal").lower(),
        requested_by_id=getattr(current_user, "id", None),
        due_date=date.fromisoformat(payload["due_date"]) if payload.get("due_date") else None,
    )
    db.session.add(work_order)

    event = MaintenanceEvent(
        org_id=org_id,
        work_order=work_order,
        event_type="STATUS_CHANGE",
        from_status=None,
        to_status="open",
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(event)

    db.session.commit()
    return jsonify(_serialize_work_order(work_order)), HTTPStatus.CREATED


@bp.post("/work-orders/<int:work_order_id>/start")
@require_roles("maintenance", "admin")
def start_work_order(work_order_id: int):
    org_id = resolve_org_id()
    work_order = MaintenanceWorkOrder.query.filter_by(org_id=org_id, id=work_order_id).first_or_404()

    if work_order.status not in {"open"}:
        return jsonify({"error": f"cannot start from status {work_order.status}"}), HTTPStatus.BAD_REQUEST

    now = datetime.now(UTC)
    work_order.status = "in_progress"
    work_order.started_at = now
    if not work_order.downtime_start:
        work_order.downtime_start = now

    event = MaintenanceEvent(
        org_id=org_id,
        work_order=work_order,
        event_type="STATUS_CHANGE",
        from_status="open",
        to_status="in_progress",
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(event)

    db.session.commit()
    return jsonify(_serialize_work_order(work_order)), HTTPStatus.OK


@bp.post("/work-orders/<int:work_order_id>/complete")
@require_roles("maintenance", "admin")
def complete_work_order(work_order_id: int):
    org_id = resolve_org_id()
    work_order = MaintenanceWorkOrder.query.filter_by(org_id=org_id, id=work_order_id).first_or_404()

    if work_order.status not in {"open", "in_progress"}:
        return jsonify({"error": f"cannot complete from status {work_order.status}"}), HTTPStatus.BAD_REQUEST

    now = datetime.now(UTC)
    work_order.status = "completed"
    work_order.completed_at = now

    payload = request.get_json(silent=True) or {}
    if "labor_cost" in payload:
        work_order.labor_cost = _parse_decimal(payload.get("labor_cost"))
    if "material_cost" in payload:
        work_order.material_cost = _parse_decimal(payload.get("material_cost"))
    if "other_cost" in payload:
        work_order.other_cost = _parse_decimal(payload.get("other_cost"))
    work_order.recompute_total_cost()

    if work_order.downtime_start and not work_order.downtime_end:
        work_order.downtime_end = now
        delta = work_order.downtime_end - work_order.downtime_start
        work_order.downtime_minutes = int(delta.total_seconds() // 60)

    event = MaintenanceEvent(
        org_id=org_id,
        work_order=work_order,
        event_type="STATUS_CHANGE",
        from_status=None,
        to_status="completed",
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(event)

    db.session.commit()
    return jsonify(_serialize_work_order(work_order)), HTTPStatus.OK


@bp.get("/work-orders")
@require_roles("maintenance", "admin")
def list_work_orders():
    """Return recent work orders for the current organisation.

    Optional query parameters:
    - status: filter by status
    - limit: number of rows (default 200)
    """

    org_id = resolve_org_id()
    status_filter = request.args.get("status")
    limit = int(request.args.get("limit", "200"))

    query = MaintenanceWorkOrder.query.filter_by(org_id=org_id)
    if status_filter:
        query = query.filter(MaintenanceWorkOrder.status == status_filter)

    query = query.order_by(MaintenanceWorkOrder.requested_at.desc()).limit(max(1, min(limit, 500)))
    return jsonify([_serialize_work_order(wo) for wo in query.all()]), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Escalation rules & events
# ---------------------------------------------------------------------------


def _serialize_escalation_rule(rule: MaintenanceEscalationRule) -> dict[str, Any]:
    return {
        "id": rule.id,
        "name": rule.name,
        "asset_category": rule.asset_category,
        "asset_id": rule.asset_id,
        "min_priority": rule.min_priority,
        "downtime_threshold_minutes": rule.downtime_threshold_minutes,
        "notify_role": rule.notify_role,
        "notify_channel": rule.notify_channel,
        "is_active": rule.is_active,
        "created_at": rule.created_at.isoformat(),
    }


@bp.get("/escalation-rules")
@require_roles("maintenance", "admin")
def list_escalation_rules():
    org_id = resolve_org_id()
    rules = (
        MaintenanceEscalationRule.query.filter_by(org_id=org_id)
        .order_by(MaintenanceEscalationRule.name.asc())
        .all()
    )
    return jsonify([_serialize_escalation_rule(rule) for rule in rules]), HTTPStatus.OK


@bp.post("/escalation-rules")
@require_roles("maintenance", "admin")
def create_escalation_rule():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), HTTPStatus.BAD_REQUEST

    try:
        threshold = int(payload.get("downtime_threshold_minutes", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "downtime_threshold_minutes must be an integer"}), HTTPStatus.BAD_REQUEST
    if threshold <= 0:
        return jsonify({"error": "downtime_threshold_minutes must be greater than zero"}), HTTPStatus.BAD_REQUEST

    rule = MaintenanceEscalationRule(
        org_id=org_id,
        name=name,
        asset_category=(payload.get("asset_category") or "").strip() or None,
        asset_id=payload.get("asset_id"),
        min_priority=(payload.get("min_priority") or "normal").lower(),
        downtime_threshold_minutes=threshold,
        notify_role=(payload.get("notify_role") or "").strip() or None,
        notify_channel=(payload.get("notify_channel") or "telegram").lower(),
        is_active=bool(payload.get("is_active", True)),
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify(_serialize_escalation_rule(rule)), HTTPStatus.CREATED


@bp.get("/work-orders/<int:work_order_id>/events")
@require_roles("maintenance", "admin")
def list_work_order_events(work_order_id: int):
    org_id = resolve_org_id()
    work_order = MaintenanceWorkOrder.query.filter_by(org_id=org_id, id=work_order_id).first_or_404()
    events = [
        {
            "id": event.id,
            "event_type": event.event_type,
            "message": event.message,
            "from_status": event.from_status,
            "to_status": event.to_status,
            "created_at": event.created_at.isoformat(),
            "created_by_id": event.created_by_id,
        }
        for event in work_order.events
    ]
    return jsonify(events), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Sensor readings
# ---------------------------------------------------------------------------


@bp.post("/assets/<int:asset_id>/sensor-readings")
@require_roles("maintenance", "admin")
def record_sensor_reading(asset_id: int):
    org_id = resolve_org_id()
    asset = MaintenanceAsset.query.filter_by(org_id=org_id, id=asset_id).first_or_404()

    payload = request.get_json(silent=True) or {}
    sensor_type = (payload.get("sensor_type") or "").strip()
    if not sensor_type:
        return jsonify({"error": "sensor_type is required"}), HTTPStatus.BAD_REQUEST

    reading = MaintenanceSensorReading(
        org_id=org_id,
        asset_id=asset.id,
        sensor_type=sensor_type,
        value=_parse_decimal(payload.get("value"), default="0"),
        unit=(payload.get("unit") or "").strip() or None,
        raw_payload=payload.get("raw_payload") or None,
    )
    db.session.add(reading)
    db.session.commit()

    return (
        jsonify(
            {
                "id": reading.id,
                "sensor_type": reading.sensor_type,
                "value": float(reading.value or 0),
                "unit": reading.unit,
                "recorded_at": reading.recorded_at.isoformat(),
            }
        ),
        HTTPStatus.CREATED,
    )


# ---------------------------------------------------------------------------
# KPI / Analytics
# ---------------------------------------------------------------------------


@bp.get("/kpi/summary")
@require_roles("maintenance", "admin")
def kpi_summary():
    org_id = resolve_org_id()
    from_raw = request.args.get("from")
    to_raw = request.args.get("to")

    today = datetime.utcnow().date()
    date_from = date.fromisoformat(from_raw) if from_raw else today - timedelta(days=30)
    date_to = date.fromisoformat(to_raw) if to_raw else today

    query = MaintenanceWorkOrder.query.filter(
        MaintenanceWorkOrder.org_id == org_id,
        MaintenanceWorkOrder.requested_at >= datetime.combine(date_from, datetime.min.time()),
        MaintenanceWorkOrder.requested_at <= datetime.combine(date_to, datetime.max.time()),
        MaintenanceWorkOrder.status == "completed",
    )

    work_orders = query.all()
    if not work_orders:
        return (
            jsonify(
                {
                    "date_from": date_from.isoformat(),
                    "date_to": date_to.isoformat(),
                    "total_downtime_minutes": 0,
                    "mttr_minutes": 0,
                    "avg_response_minutes": 0,
                    "total_cost": 0.0,
                }
            ),
            HTTPStatus.OK,
        )

    total_downtime = 0
    repair_events = 0
    total_response = 0
    response_count = 0
    total_cost = Decimal("0")

    for work_order in work_orders:
        if work_order.downtime_minutes:
            total_downtime += work_order.downtime_minutes
            repair_events += 1
        if work_order.started_at:
            delta_resp = work_order.started_at - work_order.requested_at
            total_response += int(delta_resp.total_seconds() // 60)
            response_count += 1
        total_cost += work_order.total_cost or 0

    mttr = int(total_downtime / repair_events) if repair_events else 0
    avg_response = int(total_response / response_count) if response_count else 0

    return (
        jsonify(
            {
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "total_downtime_minutes": total_downtime,
                "mttr_minutes": mttr,
                "avg_response_minutes": avg_response,
                "total_cost": float(total_cost),
            }
        ),
        HTTPStatus.OK,
    )


__all__ = ["bp"]
