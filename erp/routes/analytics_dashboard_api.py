from __future__ import annotations

from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Dict

from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_

from erp.extensions import db
from erp.models import (
    BotJobOutbox,
    MaintenanceEscalationEvent,
    MaintenanceWorkOrder,
    Order,
)
from erp.security_decorators_phase2 import require_permission
from erp.utils import resolve_org_id

bp = Blueprint("analytics_dashboard_api", __name__, url_prefix="/api/analytics-dashboard")


@bp.get("/operations")
@require_permission("analytics", "view")
def operations_summary():
    org_id = resolve_org_id()

    now = datetime.now(UTC)
    last_7_days = now - timedelta(days=7)

    orders_7d = (
        db.session.query(func.count(Order.id))
        .filter(Order.org_id == org_id)
        .filter(Order.created_at >= last_7_days)
        .scalar()
        or 0
    )

    wo_open = (
        db.session.query(func.count(MaintenanceWorkOrder.id))
        .filter(MaintenanceWorkOrder.org_id == org_id)
        .filter(MaintenanceWorkOrder.status.in_(["open", "in_progress"]))
        .scalar()
        or 0
    )

    escalations_7d = (
        db.session.query(func.count(MaintenanceEscalationEvent.id))
        .filter(MaintenanceEscalationEvent.org_id == org_id)
        .filter(MaintenanceEscalationEvent.created_at >= last_7_days)
        .scalar()
        or 0
    )

    return (
        jsonify(
            {
                "orders_last_7_days": int(orders_7d),
                "work_orders_open_or_in_progress": int(wo_open),
                "escalations_last_7_days": int(escalations_7d),
            }
        ),
        HTTPStatus.OK,
    )


@bp.get("/bot-activity")
@require_permission("analytics", "view")
def bot_activity():
    org_id = resolve_org_id()

    now = datetime.now(UTC)
    last_24h = now - timedelta(hours=24)

    total_24h = (
        db.session.query(func.count(BotJobOutbox.id))
        .filter(BotJobOutbox.org_id == org_id)
        .filter(BotJobOutbox.created_at >= last_24h)
        .scalar()
        or 0
    )

    errors_24h = (
        db.session.query(func.count(BotJobOutbox.id))
        .filter(BotJobOutbox.org_id == org_id)
        .filter(BotJobOutbox.created_at >= last_24h)
        .filter(or_(BotJobOutbox.status == "failed", BotJobOutbox.last_error.isnot(None)))
        .scalar()
        or 0
    )

    return jsonify({"total_last_24h": int(total_24h), "errors_last_24h": int(errors_24h)}), HTTPStatus.OK


@bp.get("/executive")
@require_permission("analytics", "view")
def executive_summary():
    org_id = resolve_org_id()

    total_orders = db.session.query(func.count(Order.id)).filter(Order.org_id == org_id).scalar() or 0
    completed_orders = (
        db.session.query(func.count(Order.id))
        .filter(Order.org_id == org_id)
        .filter(Order.status.in_(["completed", "delivered"]))
        .scalar()
        or 0
    )

    total_work_orders = (
        db.session.query(func.count(MaintenanceWorkOrder.id))
        .filter(MaintenanceWorkOrder.org_id == org_id)
        .scalar()
        or 0
    )

    completed_work_orders = (
        db.session.query(func.count(MaintenanceWorkOrder.id))
        .filter(MaintenanceWorkOrder.org_id == org_id)
        .filter(MaintenanceWorkOrder.status.in_(["completed", "closed"]))
        .scalar()
        or 0
    )

    return (
        jsonify(
            {
                "orders": {"total": int(total_orders), "completed": int(completed_orders)},
                "maintenance": {"total": int(total_work_orders), "completed": int(completed_work_orders)},
            }
        ),
        HTTPStatus.OK,
    )
