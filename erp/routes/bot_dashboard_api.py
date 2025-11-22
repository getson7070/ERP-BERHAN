"""Bot activity dashboard endpoints for admins and analysts."""
from __future__ import annotations

from datetime import datetime, timedelta
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from erp.extensions import db
from erp.models import BotEvent, BotJobOutbox
from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("bot_dashboard_api", __name__, url_prefix="/api/bot-dashboard")


@bp.get("/summary")
@require_roles("admin", "analytics")
def summary():
    org_id = resolve_org_id()

    cutoff = datetime.utcnow() - timedelta(hours=24)
    last_24h = db.session.query(func.count(BotEvent.id)).filter(
        BotEvent.org_id == org_id,
        BotEvent.created_at >= cutoff,
    ).scalar()

    errors_24h = db.session.query(func.count(BotEvent.id)).filter(
        BotEvent.org_id == org_id,
        BotEvent.event_type == "error",
        BotEvent.created_at >= cutoff,
    ).scalar()

    queued = BotJobOutbox.query.filter_by(org_id=org_id, status="queued").count()
    failed = BotJobOutbox.query.filter_by(org_id=org_id, status="failed").count()

    return (
        jsonify(
            {
                "events_last_24h": int(last_24h or 0),
                "errors_last_24h": int(errors_24h or 0),
                "jobs_queued": queued,
                "jobs_failed": failed,
            }
        ),
        HTTPStatus.OK,
    )


@bp.get("/events")
@require_roles("admin", "analytics")
def events():
    org_id = resolve_org_id()
    bot_name = request.args.get("bot_name")
    event_type = request.args.get("event_type")

    q = BotEvent.query.filter_by(org_id=org_id)
    if bot_name:
        q = q.filter_by(bot_name=bot_name)
    if event_type:
        q = q.filter_by(event_type=event_type)

    rows = q.order_by(BotEvent.id.desc()).limit(500).all()
    return (
        jsonify(
            [
                {
                    "id": r.id,
                    "bot_name": r.bot_name,
                    "event_type": r.event_type,
                    "severity": r.severity,
                    "actor_id": r.actor_id,
                    "created_at": r.created_at.isoformat(),
                    "payload": r.payload_json,
                }
                for r in rows
            ]
        ),
        HTTPStatus.OK,
    )
