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
from erp.procurement.models import ProcurementTicket
from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("analytics_dashboard_api", __name__, url_prefix="/api/analytics-dash")


@bp.get("/operations")
@require_roles("admin", "analytics", "management", "supervisor")
def operations_summary():
    """Return geo heartbeat and escalation health for the active org.

    Supports an optional `hours` query parameter (1-168) to tune the geo
    freshness window used for stale check-ins.
    """

    org_id = resolve_org_id()
    hours_param = request.args.get("hours", type=int)
    lookback_hours = hours_param if hours_param is not None else 24
    if lookback_hours < 1 or lookback_hours > 168:
        return jsonify({"error": "invalid_hours", "hint": "use 1-168 hours"}), HTTPStatus.BAD_REQUEST

    now = datetime.now(UTC)
    stale_cutoff = now - timedelta(hours=lookback_hours)

    total_escalations = MaintenanceEscalationEvent.query.filter_by(org_id=org_id).count()
    open_escalations = (
        MaintenanceEscalationEvent.query.filter_by(org_id=org_id)
        .filter(MaintenanceEscalationEvent.status != "resolved")
        .count()
    )
    resolved_escalations = (
        MaintenanceEscalationEvent.query.filter_by(org_id=org_id, status="resolved").count()
    )

    active_work_orders = MaintenanceWorkOrder.query.filter_by(org_id=org_id).filter(
        MaintenanceWorkOrder.status != "closed"
    )

    stale_geo = (
        active_work_orders.filter(
            or_(
                MaintenanceWorkOrder.last_check_in_at.is_(None),
                MaintenanceWorkOrder.last_check_in_at < stale_cutoff,
            )
        )
        .count()
    )
    healthy_geo = active_work_orders.filter(
        MaintenanceWorkOrder.last_check_in_at >= stale_cutoff
    ).count()
    sla_at_risk = active_work_orders.filter(MaintenanceWorkOrder.sla_status != "ok").count()

    payload = {
        "maintenance_escalations": {
            "open": int(open_escalations),
            "resolved": int(resolved_escalations),
            "total": int(total_escalations),
        },
        "geo_offline": {
            "stale_work_orders": int(stale_geo),
            "recent_checkins": int(healthy_geo),
            "lookback_hours": int(lookback_hours),
        },
        "sla": {"at_risk": int(sla_at_risk)},
        "captured_at": now.isoformat(),
    }
    return jsonify(payload), HTTPStatus.OK


@bp.get("/bot-activity")
@require_roles("admin", "analytics", "management", "supervisor")
def bot_activity():
    org_id = resolve_org_id()
    rows = (
        db.session.query(BotJobOutbox.status, func.count())
        .filter_by(org_id=org_id)
        .group_by(BotJobOutbox.status)
        .all()
    )
    counts: Dict[str, int] = {status: int(count) for status, count in rows}
    total = sum(counts.values())
    queued = counts.get("queued", 0)
    failed = counts.get("failed", 0)
    successful = max(total - failed - queued, 0)

    payload = {
        "total": total,
        "queued": queued,
        "failed": failed,
        "successful": successful,
        "by_status": counts,
    }
    return jsonify(payload), HTTPStatus.OK


@bp.get("/executive")
@require_roles("admin", "analytics", "management", "supervisor")
def executive_summary():
    """Cross-domain executive snapshot for the active organisation."""

    org_id = resolve_org_id()

    # Orders snapshot
    order_q = Order.query.filter_by(organization_id=org_id)
    order_counts = order_q.with_entities(func.count()).scalar() or 0
    total_order_amount = order_q.with_entities(func.coalesce(func.sum(Order.total_amount), 0)).scalar() or 0
    approved_orders = order_q.filter(Order.status.in_(["approved", "delivered", "paid", "settled"])).count()
    pending_orders = order_q.filter(Order.status.in_(["submitted", "pending"])).count()
    commission_eligible = order_q.filter(Order.commission_status == "eligible").count()
    commission_blocked = order_q.filter(Order.commission_status == "blocked").count()

    # Procurement snapshot
    procurement_q = ProcurementTicket.query.filter_by(organization_id=org_id)
    procurement_counts = procurement_q.with_entities(func.count()).scalar() or 0
    procurement_open = procurement_q.filter(ProcurementTicket.status.notin_(
        ["closed", "cancelled", "landed"]
    )).count()
    procurement_breached = procurement_q.filter(ProcurementTicket.breached_at.isnot(None)).count()

    # Maintenance snapshot
    maintenance_q = MaintenanceWorkOrder.query.filter_by(org_id=org_id)
    maintenance_open = maintenance_q.filter(MaintenanceWorkOrder.status != "closed").count()
    maintenance_sla_risk = maintenance_q.filter(MaintenanceWorkOrder.sla_status != "ok").count()

    # Bot throughput
    bot_rows = (
        BotJobOutbox.query.filter_by(org_id=org_id)
        .with_entities(BotJobOutbox.status, func.count())
        .group_by(BotJobOutbox.status)
        .all()
    )
    bot_counts = {status: int(count) for status, count in bot_rows}

    payload = {
        "orders": {
            "total": int(order_counts),
            "approved": int(approved_orders),
            "pending": int(pending_orders),
            "commission": {
                "eligible": int(commission_eligible),
                "blocked": int(commission_blocked),
            },
            "total_amount": float(total_order_amount),
        },
        "procurement": {
            "total": int(procurement_counts),
            "open": int(procurement_open),
            "sla_breached": int(procurement_breached),
        },
        "maintenance": {
            "open": int(maintenance_open),
            "sla_at_risk": int(maintenance_sla_risk),
        },
        "bots": bot_counts,
    }
    return jsonify(payload), HTTPStatus.OK


__all__ = ["bp"]
