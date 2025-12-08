from __future__ import annotations

from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Dict

from flask import Blueprint, jsonify
from sqlalchemy import func, or_

from erp.extensions import db
from erp.models import BotJobOutbox, MaintenanceEscalationEvent, MaintenanceWorkOrder
from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("analytics_dashboard_api", __name__, url_prefix="/api/analytics-dash")


@bp.get("/operations")
@require_roles("admin", "analytics", "management", "supervisor")
def operations_summary():
    org_id = resolve_org_id()
    now = datetime.now(UTC)
    stale_cutoff = now - timedelta(hours=24)

    total_escalations = MaintenanceEscalationEvent.query.filter_by(org_id=org_id).count()
    open_escalations = (
        MaintenanceEscalationEvent.query.filter_by(org_id=org_id)
        .filter(MaintenanceEscalationEvent.status != "resolved")
        .count()
    )

    stale_geo = (
        MaintenanceWorkOrder.query.filter_by(org_id=org_id)
        .filter(MaintenanceWorkOrder.status != "closed")
        .filter(
            or_(
                MaintenanceWorkOrder.last_check_in_at.is_(None),
                MaintenanceWorkOrder.last_check_in_at < stale_cutoff,
            )
        )
        .count()
    )
    healthy_geo = (
        MaintenanceWorkOrder.query.filter_by(org_id=org_id)
        .filter(MaintenanceWorkOrder.status != "closed")
        .filter(MaintenanceWorkOrder.last_check_in_at >= stale_cutoff)
        .count()
    )

    payload = {
        "maintenance_escalations": {
            "open": int(open_escalations),
            "total": int(total_escalations),
        },
        "geo_offline": {
            "stale_work_orders": int(stale_geo),
            "recent_checkins": int(healthy_geo),
            "lookback_hours": 24,
        },
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


__all__ = ["bp"]
