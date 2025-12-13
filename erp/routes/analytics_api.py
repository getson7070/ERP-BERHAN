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
from erp.security_decorators_phase2 import require_permission
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
                names.add(str(role_name).strip().lower())
    # Some user implementations store roles as strings already
    if isinstance(rel, (list, tuple)) and rel and isinstance(rel[0], str):
        names.update({str(x).strip().lower() for x in rel if x})
    return names


def _user_has_role(user: Any, role: str) -> bool:
    return str(role).strip().lower() in _role_names(user)


@bp.get("/metrics")
@require_permission("analytics", "view")
def list_metrics():
    org_id = resolve_org_id()

    metrics = (
        AnalyticsMetric.query.filter_by(org_id=org_id)
        .order_by(AnalyticsMetric.category.asc(), AnalyticsMetric.key.asc())
        .all()
    )
    return (
        jsonify(
            [
                {
                    "id": m.id,
                    "key": m.key,
                    "name": m.name,
                    "category": m.category,
                    "description": m.description,
                    "unit": m.unit,
                    "privacy_class": m.privacy_class,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in metrics
            ]
        ),
        HTTPStatus.OK,
    )


@bp.get("/fact")
@require_permission("analytics", "view")
def query_fact():
    org_id = resolve_org_id()
    metric_key = request.args.get("metric_key")
    if not metric_key:
        return jsonify({"error": "metric_key required"}), HTTPStatus.BAD_REQUEST

    metric = AnalyticsMetric.query.filter_by(org_id=org_id, key=metric_key).first()
    if metric is None:
        return jsonify({"error": "unknown metric"}), HTTPStatus.NOT_FOUND

    # Preserve existing behaviour: sensitive/PII requires admin role.
    if metric.privacy_class in {"sensitive", "pii"} and not _user_has_role(current_user, "admin"):
        return jsonify({"error": "insufficient permission for sensitive metric"}), HTTPStatus.FORBIDDEN

    today = date.today()
    from_raw = request.args.get("from")
    to_raw = request.args.get("to")

    try:
        start = date.fromisoformat(from_raw) if from_raw else today - timedelta(days=30)
        end = date.fromisoformat(to_raw) if to_raw else today
    except ValueError:
        return jsonify({"error": "from/to must be ISO dates (YYYY-MM-DD)"}), HTTPStatus.BAD_REQUEST

    facts = (
        AnalyticsFact.query.filter_by(org_id=org_id, metric_id=metric.id)
        .filter(AnalyticsFact.fact_date >= start)
        .filter(AnalyticsFact.fact_date <= end)
        .order_by(AnalyticsFact.fact_date.asc())
        .all()
    )

    return (
        jsonify(
            {
                "metric": {
                    "key": metric.key,
                    "name": metric.name,
                    "category": metric.category,
                    "unit": metric.unit,
                    "privacy_class": metric.privacy_class,
                },
                "from": start.isoformat(),
                "to": end.isoformat(),
                "facts": [
                    {
                        "date": f.fact_date.isoformat(),
                        "value": float(f.value) if f.value is not None else None,
                        "dimensions": f.dimensions_json or {},
                    }
                    for f in facts
                ],
            }
        ),
        HTTPStatus.OK,
    )


@bp.get("/dashboards")
@require_permission("analytics", "view")
def list_dashboards():
    org_id = resolve_org_id()

    dashboards = (
        AnalyticsDashboard.query.filter_by(org_id=org_id)
        .order_by(AnalyticsDashboard.name.asc())
        .all()
    )

    out = []
    for d in dashboards:
        widgets = (
            AnalyticsWidget.query.filter_by(org_id=org_id, dashboard_id=d.id)
            .order_by(AnalyticsWidget.position.asc())
            .all()
        )
        out.append(
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "widgets": [
                    {
                        "id": w.id,
                        "type": w.widget_type,
                        "title": w.title,
                        "metric_key": w.metric_key,
                        "config": w.config_json or {},
                        "position": w.position,
                    }
                    for w in widgets
                ],
            }
        )

    return jsonify(out), HTTPStatus.OK


@bp.post("/dashboards")
@require_permission("analytics", "manage")
def create_dashboard():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), HTTPStatus.BAD_REQUEST

    d = AnalyticsDashboard(
        org_id=org_id,
        name=name,
        description=(payload.get("description") or "").strip(),
    )
    db.session.add(d)
    db.session.commit()

    return jsonify({"ok": True, "id": d.id}), HTTPStatus.CREATED


@bp.get("/metrics/summary")
@require_permission("analytics", "view")
def summary():
    org_id = resolve_org_id()

    metric_count = db.session.query(func.count(AnalyticsMetric.id)).filter(AnalyticsMetric.org_id == org_id).scalar() or 0
    fact_count = db.session.query(func.count(AnalyticsFact.id)).filter(AnalyticsFact.org_id == org_id).scalar() or 0
    dashboard_count = (
        db.session.query(func.count(AnalyticsDashboard.id))
        .filter(AnalyticsDashboard.org_id == org_id)
        .scalar()
        or 0
    )

    return (
        jsonify(
            {
                "metrics": int(metric_count),
                "facts": int(fact_count),
                "dashboards": int(dashboard_count),
            }
        ),
        HTTPStatus.OK,
    )
