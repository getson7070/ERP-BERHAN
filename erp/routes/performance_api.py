"""Performance KPIs, scorecards, cycles, and feedback endpoints."""
from __future__ import annotations

from datetime import date
from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.extensions import db
from erp.models import (
    Feedback360,
    KPIRegistry,
    PerformanceEvaluation,
    ReviewCycle,
    ScorecardItem,
    ScorecardTemplate,
)
from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("performance_api", __name__, url_prefix="/api/performance")


def _serialize_kpi(row: KPIRegistry) -> dict[str, Any]:
    return {
        "kpi_key": row.kpi_key,
        "name": row.name,
        "weight": float(row.weight),
        "target_value": float(row.target_value) if row.target_value is not None else None,
        "direction": row.direction,
    }


@bp.get("/kpis")
@require_roles("admin", "hr", "analytics")
def list_kpis():
    org_id = resolve_org_id()
    rows = KPIRegistry.query.filter_by(org_id=org_id, is_active=True).all()
    return jsonify([_serialize_kpi(r) for r in rows]), HTTPStatus.OK


@bp.post("/scorecards")
@require_roles("admin", "hr", "analytics")
def create_scorecard():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    subject_type = (payload.get("subject_type") or "").strip().lower()
    if not name or not subject_type:
        return jsonify({"error": "name and subject_type required"}), HTTPStatus.BAD_REQUEST

    template = ScorecardTemplate(
        org_id=org_id,
        name=name,
        subject_type=subject_type,
        is_default=bool(payload.get("is_default", False)),
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(template)
    db.session.flush()

    for item in payload.get("items", []) or []:
        db.session.add(
            ScorecardItem(
                org_id=org_id,
                template_id=template.id,
                kpi_key=item["kpi_key"],
                weight_override=item.get("weight_override"),
                target_override=item.get("target_override"),
            )
        )

    db.session.commit()
    return jsonify({"id": template.id}), HTTPStatus.CREATED


@bp.post("/cycles")
@require_roles("admin", "hr")
def create_cycle():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip() or "Review Cycle"
    start_raw = payload.get("start_date")
    end_raw = payload.get("end_date")
    if not start_raw or not end_raw:
        return jsonify({"error": "start_date and end_date required"}), HTTPStatus.BAD_REQUEST

    cycle = ReviewCycle(
        org_id=org_id,
        name=name,
        start_date=date.fromisoformat(start_raw),
        end_date=date.fromisoformat(end_raw),
    )
    db.session.add(cycle)
    db.session.commit()
    return jsonify({"id": cycle.id}), HTTPStatus.CREATED


@bp.get("/evaluations")
@require_roles("admin", "hr", "analytics", "manager")
def list_evaluations():
    org_id = resolve_org_id()
    args = request.args

    q = PerformanceEvaluation.query.filter_by(org_id=org_id)
    if args.get("subject_type"):
        q = q.filter_by(subject_type=args.get("subject_type"))
    if args.get("subject_id"):
        q = q.filter_by(subject_id=int(args.get("subject_id")))
    if args.get("cycle_id"):
        q = q.filter_by(cycle_id=int(args.get("cycle_id")))

    rows = q.order_by(PerformanceEvaluation.total_score.desc()).limit(500).all()

    return jsonify(
        [
            {
                "id": r.id,
                "cycle_id": r.cycle_id,
                "subject_type": r.subject_type,
                "subject_id": r.subject_id,
                "total_score": float(r.total_score),
                "breakdown": r.breakdown_json,
                "status": r.status,
            }
            for r in rows
        ]
    ), HTTPStatus.OK


@bp.post("/evaluations/<int:eval_id>/feedback")
@require_roles("admin", "hr", "manager", "employee", "client")
def add_feedback(eval_id: int):
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    feedback = Feedback360(
        org_id=org_id,
        evaluation_id=eval_id,
        giver_type="user",
        giver_id=getattr(current_user, "id", None) or 0,
        rating=payload.get("rating"),
        comment=(payload.get("comment") or "").strip() or None,
        dimension=(payload.get("dimension") or "").strip() or None,
    )
    db.session.add(feedback)
    db.session.commit()
    return jsonify({"status": "ok"}), HTTPStatus.CREATED
