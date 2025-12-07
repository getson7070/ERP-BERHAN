"""Analytics routes exposing KPI summaries and background tasks."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from statistics import fmean
from typing import Iterable, List

from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import func

from erp.analytics import DemandForecaster
from erp.extensions import db
from erp.models import (
    ActivityEvent,
    EmployeeScorecard,
    FinanceEntry,
    Inventory,
    MaintenanceTicket,
    MaintenanceWorkOrder,
    Order,
    Recommendation,
    User,
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


def _gather_activity_rollups(org_id: int, days: int = 30) -> dict[str, int]:
    cutoff = utc_now() - timedelta(days=days)
    counts = defaultdict(int)
    events = (
        ActivityEvent.query.filter(
            ActivityEvent.org_id == org_id,
            ActivityEvent.occurred_at >= cutoff,
        )
        .with_entities(ActivityEvent.action, ActivityEvent.status)
        .all()
    )
    for action, status in events:
        counts[action] += 1
        if status:
            counts[f"{action}:{status}"] += 1
    return counts


def _scorecards(org_id: int) -> list[dict[str, object]]:
    """Compute or refresh monthly employee scorecards."""

    today = date.today()
    period_start = today.replace(day=1)
    existing = {
        (sc.user_id, sc.period_start): sc
        for sc in EmployeeScorecard.query.filter_by(org_id=org_id, period_start=period_start).all()
    }

    def _get(user_id: int) -> EmployeeScorecard:
        key = (user_id, period_start)
        if key not in existing:
            existing[key] = EmployeeScorecard(
                org_id=org_id,
                user_id=user_id,
                period_start=period_start,
            )
        return existing[key]

    # Sales performance
    eligible_statuses = {"completed", "delivered", "fulfilled", "approved"}
    for order in (
        Order.query.filter(
            Order.organization_id == org_id,
            Order.assigned_sales_rep_id.isnot(None),
            Order.payment_status == "settled",
        ).all()
    ):
        sc = _get(order.assigned_sales_rep_id)
        sc.sales_total = (sc.sales_total or 0) + float(order.total_amount or 0)
        if (order.status or "").lower() in eligible_statuses:
            sc.orders_closed = (sc.orders_closed or 0) + 1

    # Maintenance fulfilment
    for wo in MaintenanceWorkOrder.query.filter_by(org_id=org_id).all():
        if wo.assigned_to_id is None:
            continue
        sc = _get(wo.assigned_to_id)
        if wo.status == "completed":
            sc.maintenance_closed = (sc.maintenance_closed or 0) + 1
        if wo.status in {"open", "in_progress"} and wo.due_date and wo.due_date < today:
            sc.overdue_tasks = (sc.overdue_tasks or 0) + 1

    # Conversion rate proxy from CRM leads
    leads = CrmLead.query.filter(CrmLead.org_id == org_id).all()
    for lead in leads:
        if not lead.order_id:
            continue
        # attribute to owner if exists in ActivityEvent metadata, else skip
        owner_id = None
        if lead.interactions:
            owner_id = lead.interactions[-1].author_id
        if owner_id:
            sc = _get(owner_id)
            sc.conversion_rate = max(float(sc.conversion_rate or 0), 0.1)

    # Track complaints via activity events
    activity_counts = _gather_activity_rollups(org_id, days=60)
    for key, count in activity_counts.items():
        if not key.startswith("complaint"):
            continue
        for sc in existing.values():
            sc.complaints = (sc.complaints or 0) + count

    # Compute composite score and persist
    results: list[EmployeeScorecard] = []
    for sc in existing.values():
        sales_score = float(sc.sales_total or 0) / 10000.0
        delivery_score = (sc.orders_closed or 0) * 1.0 + (sc.maintenance_closed or 0) * 0.5
        penalty = (sc.overdue_tasks or 0) * 0.5 + (sc.complaints or 0) * 1.0
        sc.performance_score = max(0.0, round(sales_score + delivery_score - penalty, 2))
        sc.highlights = {
            "orders_closed": sc.orders_closed or 0,
            "maintenance_closed": sc.maintenance_closed or 0,
            "overdue_tasks": sc.overdue_tasks or 0,
        }
        results.append(sc)
        db.session.add(sc)

    db.session.commit()

    user_names = {
        u.id: (u.full_name or u.username or f"User {u.id}")
        for u in User.query.filter(User.id.in_([sc.user_id for sc in results if sc.user_id])).all()
    }

    return [
        {
            "user_id": sc.user_id,
            "name": user_names.get(sc.user_id, "Unassigned"),
            "sales_total": float(sc.sales_total or 0),
            "orders_closed": sc.orders_closed or 0,
            "maintenance_closed": sc.maintenance_closed or 0,
            "overdue_tasks": sc.overdue_tasks or 0,
            "conversion_rate": round(float(sc.conversion_rate or 0), 2),
            "performance_score": float(sc.performance_score or 0),
        }
        for sc in sorted(results, key=lambda s: float(s.performance_score or 0), reverse=True)
    ]


def _generate_recommendations(org_id: int, scorecards: list[dict[str, object]]):
    suggestions: list[Recommendation] = []
    period = date.today().replace(day=1)

    for sc in scorecards:
        user_id = sc.get("user_id")
        overdue = int(sc.get("overdue_tasks", 0))
        performance = float(sc.get("performance_score", 0))
        conversion = float(sc.get("conversion_rate", 0))
        sales_total = float(sc.get("sales_total", 0))

        if overdue > 0:
            suggestions.append(
                Recommendation(
                    org_id=org_id,
                    category="sla",
                    message=f"{overdue} overdue tasks need immediate follow-up",
                    severity="warning",
                    created_for_user_id=user_id,
                    source_period=period,
                )
            )
        if performance < 1.0:
            suggestions.append(
                Recommendation(
                    org_id=org_id,
                    category="coaching",
                    message="Schedule coaching to lift performance score above 1.0",
                    severity="info",
                    created_for_user_id=user_id,
                    source_period=period,
                )
            )
        if conversion < 0.2:
            suggestions.append(
                Recommendation(
                    org_id=org_id,
                    category="conversion",
                    message="Improve lead follow-up cadence to raise conversion rates",
                    severity="info",
                    created_for_user_id=user_id,
                    source_period=period,
                )
            )
        if sales_total >= 100000:
            suggestions.append(
                Recommendation(
                    org_id=org_id,
                    category="recognition",
                    message="High sales volume achieved — nominate for commission payout",
                    severity="success",
                    created_for_user_id=user_id,
                    source_period=period,
                )
            )

    persisted: list[dict[str, object]] = []
    for rec in suggestions:
        existing = Recommendation.query.filter_by(
            org_id=org_id,
            category=rec.category,
            message=rec.message,
            created_for_user_id=rec.created_for_user_id,
            source_period=rec.source_period,
        ).first()
        if existing:
            persisted.append(
                {
                    "category": existing.category,
                    "message": existing.message,
                    "severity": existing.severity,
                    "status": existing.status,
                }
            )
            continue
        db.session.add(rec)
        persisted.append(
            {
                "category": rec.category,
                "message": rec.message,
                "severity": rec.severity,
                "status": rec.status,
            }
        )
    if suggestions:
        db.session.commit()
    return persisted


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

    scorecards = _scorecards(org_id)
    recommendations = _generate_recommendations(org_id, scorecards)

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
        "scorecards": scorecards,
        "recommendations": recommendations,
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
