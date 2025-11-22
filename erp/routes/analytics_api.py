"""Analytics API for metrics registry, facts, and dashboards."""
from __future__ import annotations

from datetime import date, timedelta
from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user
from sqlalchemy import func

from erp.extensions import db
from erp.models import AnalyticsDashboard, AnalyticsFact, AnalyticsMetric, AnalyticsWidget
from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("analytics_api", __name__, url_prefix="/api/analytics")


def _role_names(user: Any) -> set[str]:
    names: set[str] = set()
    if not user:
        return names

    rel = getattr(user, "roles", None)
    if rel:
        for role_obj in rel:
            role_name = getattr(role_obj, "name", None)
            if role_name:
                names.add(str(role_name).lower())

    for attr in ("role", "role_name"):
        val = getattr(user, attr, None)
        if isinstance(val, str):
            names.add(val.lower())

    return names


def _user_has_role(user: Any, role: str) -> bool:
    return role.lower() in _role_names(user)


def _serialize_metric(metric: AnalyticsMetric) -> dict[str, Any]:
    return {
        "key": metric.key,
        "name": metric.name,
        "unit": metric.unit,
        "type": metric.metric_type,
        "privacy_class": metric.privacy_class,
        "source_module": metric.source_module,
    }


@bp.get("/metrics")
@require_roles("analytics", "admin")
def list_metrics():
    org_id = resolve_org_id()
    q = AnalyticsMetric.query.filter_by(org_id=org_id, is_active=True)
    return jsonify([_serialize_metric(m) for m in q.all()]), HTTPStatus.OK


@bp.get("/fact")
@require_roles("analytics", "admin")
def query_fact():
    org_id = resolve_org_id()
    metric_key = request.args.get("metric_key")
    if not metric_key:
        return jsonify({"error": "metric_key required"}), HTTPStatus.BAD_REQUEST

    metric = AnalyticsMetric.query.filter_by(org_id=org_id, key=metric_key).first()
    if metric is None:
        return jsonify({"error": "unknown metric"}), HTTPStatus.NOT_FOUND

    if metric.privacy_class in {"sensitive", "pii"} and not _user_has_role(current_user, "admin"):
        return jsonify({"error": "insufficient permission for sensitive metric"}), HTTPStatus.FORBIDDEN

    today = date.today()
    from_raw = request.args.get("from")
    to_raw = request.args.get("to")
    date_from = date.fromisoformat(from_raw) if from_raw else today - timedelta(days=30)
    date_to = date.fromisoformat(to_raw) if to_raw else today

    query = AnalyticsFact.query.filter(
        AnalyticsFact.org_id == org_id,
        AnalyticsFact.metric_key == metric_key,
        AnalyticsFact.ts_date >= date_from,
        AnalyticsFact.ts_date <= date_to,
    )

    for dim in ("warehouse_id", "user_id", "client_id", "item_id", "region"):
        value = request.args.get(dim)
        if value:
            column = getattr(AnalyticsFact, dim)
            query = query.filter(column == value)

    query = query.order_by(AnalyticsFact.ts_date.asc())
    payload = [
        {"date": row.ts_date.isoformat(), "value": float(row.value)} for row in query.all()
    ]
    return jsonify(payload), HTTPStatus.OK


def _serialize_widget(widget: AnalyticsWidget) -> dict[str, Any]:
    return {
        "id": widget.id,
        "title": widget.title,
        "metric_key": widget.metric_key,
        "chart_type": widget.chart_type,
        "config": widget.config_json,
        "position": widget.position,
    }


def _serialize_dashboard(dashboard: AnalyticsDashboard) -> dict[str, Any]:
    return {
        "id": dashboard.id,
        "name": dashboard.name,
        "for_role": dashboard.for_role,
        "is_default": dashboard.is_default,
        "widgets": [_serialize_widget(w) for w in dashboard.widgets],
    }


@bp.get("/dashboards")
@require_roles("analytics", "admin")
def dashboards_for_user():
    org_id = resolve_org_id()
    roles = _role_names(current_user)
    dashboards = (
        AnalyticsDashboard.query.filter(
            AnalyticsDashboard.org_id == org_id,
            AnalyticsDashboard.is_active.is_(True),
        )
        .order_by(AnalyticsDashboard.name.asc())
        .all()
    )

    visible: list[AnalyticsDashboard] = []
    for dashboard in dashboards:
        if dashboard.for_role is None:
            visible.append(dashboard)
        elif dashboard.for_role in roles or _user_has_role(current_user, "admin"):
            visible.append(dashboard)

    return jsonify([_serialize_dashboard(d) for d in visible]), HTTPStatus.OK


@bp.post("/dashboards")
@require_roles("analytics", "admin")
def create_dashboard():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), HTTPStatus.BAD_REQUEST

    dashboard = AnalyticsDashboard(
        org_id=org_id,
        name=name,
        for_role=(payload.get("for_role") or None),
        is_default=bool(payload.get("is_default", False)),
        is_active=True,
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(dashboard)
    db.session.flush()

    widgets_payload = payload.get("widgets") or []
    for position, widget_payload in enumerate(widgets_payload):
        metric_key = (widget_payload.get("metric_key") or "").strip()
        if not metric_key:
            continue
        widget = AnalyticsWidget(
            org_id=org_id,
            dashboard_id=dashboard.id,
            title=(widget_payload.get("title") or metric_key),
            metric_key=metric_key,
            chart_type=(widget_payload.get("chart_type") or "line"),
            config_json=widget_payload.get("config") or {},
            position=position,
        )
        db.session.add(widget)

    db.session.commit()
    return jsonify(_serialize_dashboard(dashboard)), HTTPStatus.CREATED


@bp.get("/metrics/summary")
@require_roles("analytics", "admin")
def metrics_summary():
    org_id = resolve_org_id()
    counts = (
        db.session.query(
            AnalyticsMetric.privacy_class,
            func.count(AnalyticsMetric.id),
        )
        .filter(
            AnalyticsMetric.org_id == org_id,
            AnalyticsMetric.is_active.is_(True),
        )
        .group_by(AnalyticsMetric.privacy_class)
        .all()
    )
    summary = {privacy: count for privacy, count in counts}
    return jsonify(summary), HTTPStatus.OK
