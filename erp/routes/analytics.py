"""Analytics routes exposing KPI summaries and background tasks."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, List

from collections import defaultdict
from datetime import timedelta
from statistics import fmean
from typing import Iterable, List

from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import func

from erp.analytics import DemandForecaster
from erp.extensions import db
from erp.models import (
    FinanceEntry,
    Inventory,
    MaintenanceTicket,
    Order,
)
from erp.models.core_entities import AnalyticsEvent, CrmLead
from erp.utils import resolve_org_id, utc_now

bp = Blueprint("analytics", __name__, url_prefix="/analytics")


def _monthly_sales(org_id: int) -> list[dict[str, float | str]]:
    """Aggregate sales totals by month for dashboard visualisations."""

    buckets: dict[str, float] = defaultdict(float)
    orders = (
        Order.query.filter_by(organization_id=org_id)
        .order_by(Order.placed_at)
        .all()
    )
    for order in orders:
        month = order.placed_at.strftime("%Y-%m") if order.placed_at else "unknown"
        buckets[month] += float(order.total_amount or 0)
    return [
        {"month": month, "total": total}
        for month, total in sorted(buckets.items())
    ]


def _ticket_resolution_stats(org_id: int) -> tuple[float, float]:
    closed = (
        MaintenanceTicket.query.filter(
            MaintenanceTicket.org_id == org_id,
            MaintenanceTicket.closed_at.isnot(None),
            MaintenanceTicket.created_at.isnot(None),
        )
        .order_by(MaintenanceTicket.closed_at.desc())
        .limit(250)
        .all()
    )

    durations: list[float] = []
    sla_hits = 0
    for ticket in closed:
        elapsed = (ticket.closed_at - ticket.created_at).total_seconds() / 3600.0
        durations.append(elapsed)
        if elapsed <= 48:
            sla_hits += 1

    if not durations:
        return 0.0, 1.0
    return float(fmean(durations)), float(sla_hits / len(durations))


def fetch_kpis(org_id: int) -> dict[str, object]:
    """Return live KPIs sourced from the relational models."""

    pending_orders = (
        Order.query.filter_by(organization_id=org_id, status="pending").count()
    )
    open_tickets = (
        MaintenanceTicket.query.filter_by(org_id=org_id, status="open").count()
    )
    low_stock = (
        Inventory.query.filter(
            Inventory.org_id == org_id,
            Inventory.quantity <= 5,
        ).count()
    )
    pipeline_value = (
        db.session.query(func.coalesce(func.sum(CrmLead.potential_value), 0))
        .filter(CrmLead.org_id == org_id, CrmLead.status.in_(["qualified", "won"]))
        .scalar()
    )

    geo_hotspots = (
        db.session.query(AnalyticsEvent.location_label, func.count())
        .filter(
            AnalyticsEvent.org_id == org_id,
            AnalyticsEvent.location_label.isnot(None),
        )
        .group_by(AnalyticsEvent.location_label)
        .order_by(func.count().desc())
        .limit(10)
        .all()
    )

    avg_resolution_hours, sla_ratio = _ticket_resolution_stats(org_id)

    total_leads = CrmLead.query.filter(CrmLead.org_id == org_id).count()
    won_leads = (
        CrmLead.query.filter(CrmLead.org_id == org_id, CrmLead.status == "won").count()
    )
    conversion_rate = float(won_leads / total_leads) if total_leads else 0.0

    last_day = utc_now() - timedelta(hours=24)
    automation_events = (
        db.session.query(func.count(AnalyticsEvent.id))
        .filter(
            AnalyticsEvent.org_id == org_id,
            AnalyticsEvent.metric.in_(["automation", "bot_trigger"]),
            AnalyticsEvent.captured_at >= last_day,
        )
        .scalar()
    ) or 0

    return {
        "pending_orders": pending_orders,
        "open_maintenance": open_tickets,
        "low_stock_items": low_stock,
        "qualified_pipeline_value": float(pipeline_value or 0),
        "monthly_sales": _monthly_sales(org_id),
        "geo_hotspots": [
            {"label": label, "count": count}
            for label, count in geo_hotspots
            if label
        ],
        "avg_resolution_hours": round(avg_resolution_hours, 2),
        "sla_met_ratio": round(sla_ratio, 2),
        "crm_conversion_rate": round(conversion_rate, 2),
        "automation_events_today": int(automation_events),
    }


@bp.post("/vitals")
def collect_vitals():
    data = request.get_json(silent=True) or {}
    allowed = {"lcp", "fid", "cls", "ttfb", "inp"}
    if not any(k in data for k in allowed):
        return jsonify({"error": "bad schema"}), 400

    org_id = resolve_org_id()
    timestamp = utc_now()

    location_label = (data.get("location") or data.get("city") or "").strip() or None
    try:
        location_lat = float(data.get("lat")) if data.get("lat") is not None else None
        location_lng = float(data.get("lng")) if data.get("lng") is not None else None
    except (TypeError, ValueError):
        location_lat = None
        location_lng = None

    for metric, value in data.items():
        if metric not in allowed:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        db.session.add(
            AnalyticsEvent(
                org_id=org_id,
                metric=metric,
                value=numeric,
                captured_at=timestamp,
                location_label=location_label,
                location_lat=location_lat,
                location_lng=location_lng,
            )
        )
    db.session.commit()
    return "", 204


@bp.get("/")
def analytics_index():
    org_id = resolve_org_id()
    data = fetch_kpis(org_id)
    return render_template("analytics_dashboard.html", data=data)


@bp.get("/dashboard")
def dashboard_snapshot():
    org_id = resolve_org_id()
    data = fetch_kpis(org_id)
    wants_json = request.args.get("format") == "json"
    accepts_json = request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html
    if wants_json or accepts_json:
        return jsonify(data)
    return render_template("analytics_dashboard.html", data=data)


def _send_approval_reminders(users: Iterable[int] | None = None) -> int:
    org_id = resolve_org_id()
    return Order.query.filter_by(organization_id=org_id, status="pending").count()


def _forecast_sales(history: List[int] | None = None, observed: List[int] | None = None) -> float:
    org_id = resolve_org_id()
    amounts = defaultdict(list)
    for entry in (
        FinanceEntry.query.filter_by(org_id=org_id, direction="credit")
        .order_by(FinanceEntry.posted_at)
        .all()
    ):
        month = entry.posted_at.strftime("%Y-%m") if entry.posted_at else "unknown"
        amounts[month].append(float(entry.amount or 0))

    series = [sum(values) for _, values in sorted(amounts.items())]
    if not series and history:
        series = [float(v) for v in history]
    if not series:
        series = [0.0, 0.0, 0.0]
    return float(DemandForecaster().fit(series).predict_next())


class _Task:
    def __init__(self, fn):
        self.run = fn

    def __call__(self, *a, **k):
        return self.run(*a, **k)


send_approval_reminders = _Task(_send_approval_reminders)
forecast_sales = _Task(_forecast_sales)

__all__ = [
    "bp",
    "fetch_kpis",
    "collect_vitals",
    "dashboard_snapshot",
    "send_approval_reminders",
    "forecast_sales",
]
