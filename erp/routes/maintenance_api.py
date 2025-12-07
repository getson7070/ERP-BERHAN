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
    MaintenanceEscalationEvent,
    MaintenanceEvent,
    MaintenanceSchedule,
    MaintenanceSensorReading,
    MaintenanceWorkOrder,
)
from erp.audit import log_audit
from erp.security import require_roles
from erp.utils import resolve_org_id
from erp.utils.activity import log_activity_event

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
        "request_lat": work_order.request_lat,
        "request_lng": work_order.request_lng,
        "request_location_label": work_order.request_location_label,
        "start_lat": work_order.start_lat,
        "start_lng": work_order.start_lng,
        "requested_at": work_order.requested_at.isoformat(),
        "due_date": work_order.due_date.isoformat() if work_order.due_date else None,
        "started_at": work_order.started_at.isoformat() if work_order.started_at else None,
        "completed_at": work_order.completed_at.isoformat() if work_order.completed_at else None,
        "last_check_in_at": work_order.last_check_in_at.isoformat()
        if work_order.last_check_in_at
        else None,
        "sla_status": work_order.sla_status,
        "downtime_start": work_order.downtime_start.isoformat() if work_order.downtime_start else None,
        "downtime_end": work_order.downtime_end.isoformat() if work_order.downtime_end else None,
        "downtime_minutes": work_order.downtime_minutes,
        "labor_cost": float(work_order.labor_cost or 0),
        "material_cost": float(work_order.material_cost or 0),
        "other_cost": float(work_order.other_cost or 0),
        "total_cost": float(work_order.total_cost or 0),
    }


def _record_event(
    work_order: MaintenanceWorkOrder,
    event_type: str,
    message: str | None = None,
    from_status: str | None = None,
    to_status: str | None = None,
    geo_lat: float | None = None,
    geo_lng: float | None = None,
) -> MaintenanceEvent:
    event = MaintenanceEvent(
        org_id=work_order.org_id,
        work_order=work_order,
        event_type=event_type,
        message=message,
        from_status=from_status,
        to_status=to_status,
        geo_lat=geo_lat,
        geo_lng=geo_lng,
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(event)
    return event


def _priority_rank(priority: str) -> int:
    order = {"low": 1, "normal": 2, "medium": 2, "high": 3, "critical": 4}
    return order.get(priority or "normal", 2)


def _should_escalate_for_rule(
    rule: MaintenanceEscalationRule, work_order: MaintenanceWorkOrder
) -> bool:
    if not rule.is_active:
        return False
    if rule.asset_id and work_order.asset_id and rule.asset_id != work_order.asset_id:
        return False
    if rule.asset_category and work_order.asset and work_order.asset.category:
        if rule.asset_category != work_order.asset.category:
            return False
    return _priority_rank(work_order.priority) >= _priority_rank(rule.min_priority)


def _run_sla_evaluations(work_order: MaintenanceWorkOrder) -> None:
    """Trigger SLA escalation events and audit logs when thresholds breach."""

    if work_order.status == "completed":
        work_order.sla_status = "completed"
        return

    org_id = work_order.org_id
    now = datetime.now(UTC)
    sla_breached = False

    # Overdue by due_date
    if work_order.due_date and work_order.due_date < now.date():
        sla_breached = True
        _record_event(
            work_order,
            "ESCALATION",
            message="Due date passed without completion",
            from_status=work_order.status,
            to_status=work_order.status,
        )
        log_audit(
            getattr(current_user, "id", None),
            org_id,
            "maintenance.sla_overdue",
            f"work_order={work_order.id};due_date={work_order.due_date}",
        )
        log_activity_event(
            action="maintenance.sla_overdue",
            entity_type="work_order",
            entity_id=work_order.id,
            status=work_order.status,
            severity="warning",
            metadata={"due_date": str(work_order.due_date)},
        )

    rules = MaintenanceEscalationRule.query.filter_by(org_id=org_id, is_active=True).all()
    for rule in rules:
        if not _should_escalate_for_rule(rule, work_order):
            continue
        downtime_ref = work_order.downtime_start or work_order.started_at or work_order.requested_at
        if not downtime_ref:
            continue
        delta_minutes = int((now - downtime_ref).total_seconds() // 60)
        if delta_minutes < (rule.downtime_threshold_minutes or 0):
            continue

        existing = MaintenanceEscalationEvent.query.filter_by(
            org_id=org_id, rule_id=rule.id, work_order_id=work_order.id
        ).first()
        if existing:
            continue

        sla_breached = True
        escalation_event = MaintenanceEscalationEvent(
            org_id=org_id,
            rule_id=rule.id,
            work_order_id=work_order.id,
            status="triggered",
            note=(
                f"Exceeded downtime threshold ({delta_minutes}m >= {rule.downtime_threshold_minutes}m)"
            ),
            created_by_id=getattr(current_user, "id", None),
        )
        db.session.add(escalation_event)
        _record_event(
            work_order,
            "ESCALATION",
            message=f"Escalated via {rule.name} to {rule.notify_channel}",
            from_status=work_order.status,
            to_status=work_order.status,
        )
        log_audit(
            getattr(current_user, "id", None),
            org_id,
            "maintenance.sla_escalated",
            f"work_order={work_order.id};rule={rule.name};channel={rule.notify_channel}",
        )
        log_activity_event(
            action="maintenance.sla_escalated",
            entity_type="work_order",
            entity_id=work_order.id,
            status=work_order.status,
            severity="warning",
            metadata={"rule": rule.name, "channel": rule.notify_channel},
        )

    work_order.sla_status = "breached" if sla_breached else "ok"


@bp.post("/work-orders")
@require_roles("maintenance", "admin", "client", "dispatch", "sales", "marketing")
def create_work_order():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    title = (payload.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), HTTPStatus.BAD_REQUEST

    request_lat = payload.get("request_lat") or payload.get("site_lat")
    request_lng = payload.get("request_lng") or payload.get("site_lng")
    request_label = (payload.get("request_location_label") or payload.get("site_label") or "").strip() or None

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
        request_lat=request_lat,
        request_lng=request_lng,
        request_location_label=request_label,
        due_date=date.fromisoformat(payload["due_date"]) if payload.get("due_date") else None,
    )
    db.session.add(work_order)

    _record_event(
        work_order,
        "REQUEST",
        message="Maintenance request submitted",
        to_status="open",
        geo_lat=request_lat,
        geo_lng=request_lng,
    )
    _record_event(
        work_order,
        "STATUS_CHANGE",
        from_status=None,
        to_status="open",
    )

    log_activity_event(
        action="maintenance.request_created",
        entity_type="work_order",
        entity_id=work_order.id,
        status=work_order.status,
        metadata={"priority": work_order.priority, "request_location": request_label},
    )

    db.session.commit()
    _run_sla_evaluations(work_order)
    db.session.commit()
    log_audit(
        getattr(current_user, "id", None),
        org_id,
        "maintenance.work_order_requested",
        f"work_order={work_order.id};title={title}",
    )
    return jsonify(_serialize_work_order(work_order)), HTTPStatus.CREATED


@bp.post("/work-orders/<int:work_order_id>/start")
@require_roles("maintenance", "admin", "dispatch")
def start_work_order(work_order_id: int):
    org_id = resolve_org_id()
    work_order = MaintenanceWorkOrder.query.filter_by(org_id=org_id, id=work_order_id).first_or_404()

    if work_order.status not in {"open"}:
        return jsonify({"error": f"cannot start from status {work_order.status}"}), HTTPStatus.BAD_REQUEST

    now = datetime.now(UTC)
    work_order.status = "in_progress"
    work_order.started_at = now
    payload = request.get_json(silent=True) or {}
    if "start_lat" in payload or "start_lng" in payload:
        work_order.start_lat = payload.get("start_lat") or payload.get("lat")
        work_order.start_lng = payload.get("start_lng") or payload.get("lng")
    work_order.last_check_in_at = now
    if not work_order.downtime_start:
        work_order.downtime_start = now

    _record_event(
        work_order,
        "STATUS_CHANGE",
        from_status="open",
        to_status="in_progress",
        geo_lat=work_order.start_lat,
        geo_lng=work_order.start_lng,
    )

    db.session.commit()
    _run_sla_evaluations(work_order)
    db.session.commit()
    log_audit(
        getattr(current_user, "id", None),
        org_id,
        "maintenance.work_order_started",
        f"work_order={work_order.id}",
    )
    return jsonify(_serialize_work_order(work_order)), HTTPStatus.OK


@bp.post("/work-orders/<int:work_order_id>/check-in")
@require_roles("maintenance", "admin", "dispatch")
def check_in(work_order_id: int):
    """Capture on-site geo check-ins for technicians."""

    org_id = resolve_org_id()
    work_order = MaintenanceWorkOrder.query.filter_by(org_id=org_id, id=work_order_id).first_or_404()
    if work_order.status not in {"in_progress", "open"}:
        return (
            jsonify({"error": f"cannot check-in from status {work_order.status}"}),
            HTTPStatus.BAD_REQUEST,
        )

    payload = request.get_json(silent=True) or {}
    lat = payload.get("lat") or payload.get("geo_lat") or payload.get("start_lat")
    lng = payload.get("lng") or payload.get("geo_lng") or payload.get("start_lng")
    work_order.last_check_in_at = datetime.now(UTC)
    if lat is not None:
        work_order.start_lat = work_order.start_lat or lat
    if lng is not None:
        work_order.start_lng = work_order.start_lng or lng

    _record_event(
        work_order,
        "CHECK_IN",
        message="Technician checked in on site",
        from_status=work_order.status,
        to_status=work_order.status,
        geo_lat=lat,
        geo_lng=lng,
    )
    db.session.commit()
    _run_sla_evaluations(work_order)
    db.session.commit()
    log_activity_event(
        action="maintenance.check_in",
        entity_type="work_order",
        entity_id=work_order.id,
        status=work_order.status,
        metadata={"lat": lat, "lng": lng},
    )
    log_audit(
        getattr(current_user, "id", None),
        org_id,
        "maintenance.work_order_check_in",
        f"work_order={work_order.id}",
    )
    return jsonify(_serialize_work_order(work_order)), HTTPStatus.OK


@bp.post("/work-orders/<int:work_order_id>/complete")
@require_roles("maintenance", "admin", "dispatch")
def complete_work_order(work_order_id: int):
    org_id = resolve_org_id()
    work_order = MaintenanceWorkOrder.query.filter_by(org_id=org_id, id=work_order_id).first_or_404()

    if work_order.status not in {"open", "in_progress"}:
        return jsonify({"error": f"cannot complete from status {work_order.status}"}), HTTPStatus.BAD_REQUEST

    now = datetime.now(UTC)
    prev_status = work_order.status
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

    _record_event(
        work_order,
        "STATUS_CHANGE",
        from_status=prev_status,
        to_status="completed",
    )

    db.session.commit()
    _run_sla_evaluations(work_order)
    db.session.commit()
    log_activity_event(
        action="maintenance.completed",
        entity_type="work_order",
        entity_id=work_order.id,
        status=work_order.status,
        metadata={
            "labor_cost": float(work_order.labor_cost or 0),
            "material_cost": float(work_order.material_cost or 0),
        },
    )
    log_audit(
        getattr(current_user, "id", None),
        org_id,
        "maintenance.work_order_completed",
        f"work_order={work_order.id}",
    )
    return jsonify(_serialize_work_order(work_order)), HTTPStatus.OK


@bp.get("/work-orders")
@require_roles("maintenance", "admin", "client", "dispatch")
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
    work_orders = query.all()
    for wo in work_orders:
        _run_sla_evaluations(wo)
    db.session.commit()
    return jsonify([_serialize_work_order(wo) for wo in work_orders]), HTTPStatus.OK


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
@require_roles("maintenance", "admin", "client", "dispatch")
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
            "geo_lat": event.geo_lat,
            "geo_lng": event.geo_lng,
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
