"""Maintenance API covering assets, schedules, work orders, and KPIs."""
from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
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
from erp.security_decorators_phase2 import require_permission
from erp.services.geo_utils import get_geo_data_from_request
from erp.services.notification_service import notify_escalation
from erp.utils import resolve_org_id

bp = Blueprint("maintenance_api", __name__, url_prefix="/api/maintenance")


def _serialize_asset(asset: MaintenanceAsset) -> dict[str, Any]:
    return {
        "id": asset.id,
        "code": asset.code,
        "name": asset.name,
        "serial_number": asset.serial_number,
        "model": asset.model,
        "manufacturer": asset.manufacturer,
        "category": asset.category,
        "department": asset.department,
        "location": asset.location,
        "institution_id": asset.institution_id,
        "purchase_date": asset.purchase_date.isoformat() if asset.purchase_date else None,
        "warranty_end": asset.warranty_end.isoformat() if asset.warranty_end else None,
        "status": asset.status,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
    }


def _serialize_schedule(schedule: MaintenanceSchedule) -> dict[str, Any]:
    return {
        "id": schedule.id,
        "asset_id": schedule.asset_id,
        "name": schedule.name,
        "schedule_type": schedule.schedule_type,
        "interval_days": schedule.interval_days,
        "interval_hours": schedule.interval_hours,
        "interval_minutes": schedule.interval_minutes,
        "next_due_date": schedule.next_due_date.isoformat() if schedule.next_due_date else None,
        "sla_minutes": schedule.sla_minutes,
        "active": schedule.active,
        "last_completed_date": schedule.last_completed_date.isoformat() if schedule.last_completed_date else None,
        "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
        "updated_at": schedule.updated_at.isoformat() if schedule.updated_at else None,
    }


def _serialize_work_order(work_order: MaintenanceWorkOrder) -> dict[str, Any]:
    now = datetime.now(UTC)

    sla_due_minutes: int | None = None
    if work_order.due_date:
        sla_due_at = datetime.combine(work_order.due_date, time(23, 59, tzinfo=UTC))
        delta = sla_due_at - now
        sla_due_minutes = int(delta.total_seconds() // 60)

    return {
        "id": work_order.id,
        "asset_id": work_order.asset_id,
        "schedule_id": work_order.schedule_id,
        "work_type": work_order.work_type,
        "title": work_order.title,
        "description": work_order.description,
        "status": work_order.status,
        "priority": work_order.priority,
        "requested_at": work_order.requested_at.isoformat() if work_order.requested_at else None,
        "due_date": work_order.due_date.isoformat() if work_order.due_date else None,
        "started_at": work_order.started_at.isoformat() if work_order.started_at else None,
        "completed_at": work_order.completed_at.isoformat() if work_order.completed_at else None,
        "assigned_to_id": work_order.assigned_to_id,
        "requested_by_id": work_order.requested_by_id,
        "institution_id": work_order.institution_id,
        "site_lat": work_order.site_lat,
        "site_lng": work_order.site_lng,
        "site_geo_accuracy_m": work_order.site_geo_accuracy_m,
        "sla_status": work_order.sla_status,
        "sla_due_minutes": sla_due_minutes,
        "created_at": work_order.created_at.isoformat() if work_order.created_at else None,
        "updated_at": work_order.updated_at.isoformat() if work_order.updated_at else None,
    }


def _serialize_escalation_rule(rule: MaintenanceEscalationRule) -> dict[str, Any]:
    return {
        "id": rule.id,
        "name": rule.name,
        "active": rule.active,
        "priority_min": rule.priority_min,
        "priority_max": rule.priority_max,
        "minutes_after_due": rule.minutes_after_due,
        "notify_role": rule.notify_role,
        "notify_telegram_chat_id": rule.notify_telegram_chat_id,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


def _serialize_event(ev: MaintenanceEvent) -> dict[str, Any]:
    return {
        "id": ev.id,
        "work_order_id": ev.work_order_id,
        "event_type": ev.event_type,
        "message": ev.message,
        "old_status": ev.old_status,
        "new_status": ev.new_status,
        "created_at": ev.created_at.isoformat() if ev.created_at else None,
        "created_by_id": ev.created_by_id,
        "geo_lat": ev.geo_lat,
        "geo_lng": ev.geo_lng,
        "geo_accuracy_m": ev.geo_accuracy_m,
    }


@bp.get("/assets")
@require_permission("maintenance_assets", "view")
def list_assets():
    org_id = resolve_org_id()
    q = (
        MaintenanceAsset.query.filter_by(org_id=org_id)
        .order_by(MaintenanceAsset.name.asc())
    )
    return jsonify([_serialize_asset(a) for a in q.all()]), HTTPStatus.OK


@bp.post("/assets")
@require_permission("maintenance_assets", "create")
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
        serial_number=(payload.get("serial_number") or "").strip(),
        model=(payload.get("model") or "").strip(),
        manufacturer=(payload.get("manufacturer") or "").strip(),
        category=(payload.get("category") or "").strip(),
        department=(payload.get("department") or "").strip(),
        location=(payload.get("location") or "").strip(),
        institution_id=payload.get("institution_id"),
        status=(payload.get("status") or "active").strip().lower(),
    )

    purchase_date = payload.get("purchase_date")
    if purchase_date:
        try:
            asset.purchase_date = date.fromisoformat(str(purchase_date))
        except ValueError:
            return jsonify({"error": "purchase_date must be ISO format (YYYY-MM-DD)"}), HTTPStatus.BAD_REQUEST

    warranty_end = payload.get("warranty_end")
    if warranty_end:
        try:
            asset.warranty_end = date.fromisoformat(str(warranty_end))
        except ValueError:
            return jsonify({"error": "warranty_end must be ISO format (YYYY-MM-DD)"}), HTTPStatus.BAD_REQUEST

    db.session.add(asset)
    db.session.commit()

    return jsonify(_serialize_asset(asset)), HTTPStatus.CREATED


@bp.post("/assets/<int:asset_id>/schedules")
@require_permission("maintenance_assets", "create_schedule")
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
        interval_days=int(payload.get("interval_days") or 0),
        interval_hours=int(payload.get("interval_hours") or 0),
        interval_minutes=int(payload.get("interval_minutes") or 0),
        sla_minutes=int(payload.get("sla_minutes") or 0) if payload.get("sla_minutes") is not None else None,
        active=bool(payload.get("active", True)),
    )

    next_due_date = payload.get("next_due_date")
    if next_due_date:
        try:
            schedule.next_due_date = date.fromisoformat(str(next_due_date))
        except ValueError:
            return jsonify({"error": "next_due_date must be ISO format (YYYY-MM-DD)"}), HTTPStatus.BAD_REQUEST

    db.session.add(schedule)
    db.session.commit()

    return jsonify(_serialize_schedule(schedule)), HTTPStatus.CREATED


@bp.post("/work-orders")
@require_permission("maintenance_work_orders", "create")
def create_work_order():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    asset_id = payload.get("asset_id")
    if not asset_id:
        return jsonify({"error": "asset_id is required"}), HTTPStatus.BAD_REQUEST

    asset = MaintenanceAsset.query.filter_by(org_id=org_id, id=asset_id).first()
    if asset is None:
        return jsonify({"error": "asset not found"}), HTTPStatus.NOT_FOUND

    schedule_id = payload.get("schedule_id")
    schedule = None
    if schedule_id:
        schedule = MaintenanceSchedule.query.filter_by(org_id=org_id, id=schedule_id, asset_id=asset.id).first()
        if schedule is None:
            return jsonify({"error": "schedule not found"}), HTTPStatus.NOT_FOUND

    title = (payload.get("title") or "").strip()
    description = (payload.get("description") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), HTTPStatus.BAD_REQUEST

    work_type = (payload.get("work_type") or "corrective").strip().lower()
    status = (payload.get("status") or "open").strip().lower()
    priority = (payload.get("priority") or "normal").strip().lower()

    due_date_raw = payload.get("due_date")
    due_date_value = None
    if due_date_raw:
        try:
            due_date_value = date.fromisoformat(str(due_date_raw))
        except ValueError:
            return jsonify({"error": "due_date must be ISO format (YYYY-MM-DD)"}), HTTPStatus.BAD_REQUEST

    # Geo capture (optional in current design; will be enforced in Layer 5 SLA/Geo step)
    geo = get_geo_data_from_request(payload)
    site_lat = geo.get("lat")
    site_lng = geo.get("lng")
    site_acc = geo.get("accuracy_m")

    work_order = MaintenanceWorkOrder(
        org_id=org_id,
        asset_id=asset.id,
        schedule_id=schedule.id if schedule else None,
        work_type=work_type,
        title=title,
        description=description,
        status=status,
        priority=priority,
        requested_at=datetime.now(UTC),
        due_date=due_date_value,
        requested_by_id=getattr(current_user, "id", None),
        assigned_to_id=payload.get("assigned_to_id"),
        institution_id=payload.get("institution_id") or asset.institution_id,
        site_lat=site_lat,
        site_lng=site_lng,
        site_geo_accuracy_m=site_acc,
    )

    db.session.add(work_order)
    db.session.flush()

    ev = MaintenanceEvent(
        org_id=org_id,
        work_order_id=work_order.id,
        event_type="created",
        message="Work order created",
        old_status=None,
        new_status=work_order.status,
        created_at=datetime.now(UTC),
        created_by_id=getattr(current_user, "id", None),
        geo_lat=site_lat,
        geo_lng=site_lng,
        geo_accuracy_m=site_acc,
    )
    db.session.add(ev)
    db.session.commit()

    return jsonify(_serialize_work_order(work_order)), HTTPStatus.CREATED


@bp.post("/work-orders/<int:work_order_id>/start")
@require_permission("maintenance_work_orders", "start")
def start_work_order(work_order_id: int):
    org_id = resolve_org_id()
    work_order = MaintenanceWorkOrder.query.filter_by(org_id=org_id, id=work_order_id).first_or_404()

    if work_order.status in {"completed", "closed"}:
        return jsonify({"error": "work order already completed/closed"}), HTTPStatus.CONFLICT

    payload = request.get_json(silent=True) or {}
    geo = get_geo_data_from_request(payload)
    lat = geo.get("lat")
    lng = geo.get("lng")
    acc = geo.get("accuracy_m")

    old = work_order.status
    work_order.status = "in_progress"
    work_order.started_at = datetime.now(UTC)

    ev = MaintenanceEvent(
        org_id=org_id,
        work_order_id=work_order.id,
        event_type="started",
        message="Work order started",
        old_status=old,
        new_status=work_order.status,
        created_at=datetime.now(UTC),
        created_by_id=getattr(current_user, "id", None),
        geo_lat=lat,
        geo_lng=lng,
        geo_accuracy_m=acc,
    )
    db.session.add(ev)
    db.session.commit()

    return jsonify(_serialize_work_order(work_order)), HTTPStatus.OK


@bp.post("/work-orders/<int:work_order_id>/check-in")
@require_permission("maintenance_work_orders", "checkin")
def check_in(work_order_id: int):
    org_id = resolve_org_id()
    work_order = MaintenanceWorkOrder.query.filter_by(org_id=org_id, id=work_order_id).first_or_404()

    if work_order.status not in {"in_progress", "open"}:
        return jsonify({"error": "work order is not open or in progress"}), HTTPStatus.CONFLICT

    payload = request.get_json(silent=True) or {}
    geo = get_geo_data_from_request(payload)
    lat = geo.get("lat")
    lng = geo.get("lng")
    acc = geo.get("accuracy_m")

    work_order.last_check_in_at = datetime.now(UTC)

    ev = MaintenanceEvent(
        org_id=org_id,
        work_order_id=work_order.id,
        event_type="check_in",
        message=(payload.get("message") or "Check-in recorded"),
        old_status=work_order.status,
        new_status=work_order.status,
        created_at=datetime.now(UTC),
        created_by_id=getattr(current_user, "id", None),
        geo_lat=lat,
        geo_lng=lng,
        geo_accuracy_m=acc,
    )
    db.session.add(ev)
    db.session.commit()

    return jsonify({"ok": True}), HTTPStatus.OK


@bp.post("/work-orders/<int:work_order_id>/complete")
@require_permission("maintenance_work_orders", "complete")
def complete_work_order(work_order_id: int):
    org_id = resolve_org_id()
    work_order = MaintenanceWorkOrder.query.filter_by(org_id=org_id, id=work_order_id).first_or_404()

    if work_order.status in {"completed", "closed"}:
        return jsonify({"error": "work order already completed/closed"}), HTTPStatus.CONFLICT

    payload = request.get_json(silent=True) or {}
    geo = get_geo_data_from_request(payload)
    lat = geo.get("lat")
    lng = geo.get("lng")
    acc = geo.get("accuracy_m")

    old = work_order.status
    work_order.status = "completed"
    work_order.completed_at = datetime.now(UTC)

    ev = MaintenanceEvent(
        org_id=org_id,
        work_order_id=work_order.id,
        event_type="completed",
        message=(payload.get("message") or "Work order completed"),
        old_status=old,
        new_status=work_order.status,
        created_at=datetime.now(UTC),
        created_by_id=getattr(current_user, "id", None),
        geo_lat=lat,
        geo_lng=lng,
        geo_accuracy_m=acc,
    )
    db.session.add(ev)
    db.session.commit()

    return jsonify(_serialize_work_order(work_order)), HTTPStatus.OK


@bp.get("/work-orders")
@require_permission("maintenance_work_orders", "view")
def list_work_orders():
    org_id = resolve_org_id()
    q = MaintenanceWorkOrder.query.filter_by(org_id=org_id).order_by(MaintenanceWorkOrder.id.desc()).limit(500)
    return jsonify([_serialize_work_order(wo) for wo in q.all()]), HTTPStatus.OK


@bp.get("/escalation-rules")
@require_permission("maintenance_work_orders", "manage_escalations")
def list_escalation_rules():
    org_id = resolve_org_id()
    q = MaintenanceEscalationRule.query.filter_by(org_id=org_id).order_by(MaintenanceEscalationRule.id.desc())
    return jsonify([_serialize_escalation_rule(r) for r in q.all()]), HTTPStatus.OK


@bp.post("/escalation-rules")
@require_permission("maintenance_work_orders", "manage_escalations")
def create_escalation_rule():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), HTTPStatus.BAD_REQUEST

    rule = MaintenanceEscalationRule(
        org_id=org_id,
        name=name,
        active=bool(payload.get("active", True)),
        priority_min=(payload.get("priority_min") or "").strip(),
        priority_max=(payload.get("priority_max") or "").strip(),
        minutes_after_due=int(payload.get("minutes_after_due") or 0),
        notify_role=(payload.get("notify_role") or "management_supervisor").strip(),
        notify_telegram_chat_id=(payload.get("notify_telegram_chat_id") or "").strip() or None,
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify(_serialize_escalation_rule(rule)), HTTPStatus.CREATED


@bp.get("/work-orders/<int:work_order_id>/events")
@require_permission("maintenance_events", "view")
def list_work_order_events(work_order_id: int):
    org_id = resolve_org_id()
    work_order = MaintenanceWorkOrder.query.filter_by(org_id=org_id, id=work_order_id).first_or_404()
    q = (
        MaintenanceEvent.query.filter_by(org_id=org_id, work_order_id=work_order.id)
        .order_by(MaintenanceEvent.id.asc())
        .limit(1000)
    )
    return jsonify([_serialize_event(e) for e in q.all()]), HTTPStatus.OK


@bp.post("/assets/<int:asset_id>/sensor-readings")
@require_permission("maintenance_assets", "record_sensor_reading")
def record_sensor_reading(asset_id: int):
    org_id = resolve_org_id()
    asset = MaintenanceAsset.query.filter_by(org_id=org_id, id=asset_id).first_or_404()

    payload = request.get_json(silent=True) or {}
    reading_type = (payload.get("reading_type") or "").strip()
    value = payload.get("value")
    unit = (payload.get("unit") or "").strip()
    recorded_at_raw = payload.get("recorded_at")

    if not reading_type:
        return jsonify({"error": "reading_type is required"}), HTTPStatus.BAD_REQUEST

    try:
        value_dec = Decimal(str(value))
    except Exception:
        return jsonify({"error": "value must be numeric"}), HTTPStatus.BAD_REQUEST

    recorded_at = datetime.now(UTC)
    if recorded_at_raw:
        try:
            recorded_at = datetime.fromisoformat(str(recorded_at_raw))
        except ValueError:
            return jsonify({"error": "recorded_at must be ISO datetime"}), HTTPStatus.BAD_REQUEST

    sensor = MaintenanceSensorReading(
        org_id=org_id,
        asset_id=asset.id,
        reading_type=reading_type,
        value=value_dec,
        unit=unit,
        recorded_at=recorded_at,
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(sensor)
    db.session.commit()

    return jsonify({"ok": True, "id": sensor.id}), HTTPStatus.CREATED


@bp.get("/kpi/summary")
@require_permission("analytics", "view")
def kpi_summary():
    org_id = resolve_org_id()

    open_count = MaintenanceWorkOrder.query.filter_by(org_id=org_id, status="open").count()
    in_progress_count = MaintenanceWorkOrder.query.filter_by(org_id=org_id, status="in_progress").count()
    completed_count = MaintenanceWorkOrder.query.filter_by(org_id=org_id, status="completed").count()

    return jsonify(
        {
            "open": open_count,
            "in_progress": in_progress_count,
            "completed": completed_count,
        }
    ), HTTPStatus.OK
