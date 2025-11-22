"""Reliability reporting endpoints."""
from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify

from erp.models import Incident
from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("reliability_api", __name__, url_prefix="/api/reliability")


@bp.get("/mttr")
@require_roles("admin", "analytics")
def mttr():
    org_id = resolve_org_id()
    rows = Incident.query.filter_by(org_id=org_id, status="recovered").all()
    if not rows:
        return jsonify({"mttr_minutes": None, "count": 0}), HTTPStatus.OK

    durations = []
    for row in rows:
        if row.recovered_at:
            durations.append((row.recovered_at - row.started_at).total_seconds() / 60)

    avg = sum(durations) / len(durations) if durations else None
    return jsonify({"mttr_minutes": avg, "count": len(durations)}), HTTPStatus.OK
