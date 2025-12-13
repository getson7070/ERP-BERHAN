from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify, request

from erp.models import AuditLog
from erp.security_decorators_phase2 import require_permission
from erp.services.audit_export import export_audit_logs
from erp.utils import resolve_org_id

bp = Blueprint("audit_api", __name__, url_prefix="/api/audit")


@bp.get("/logs")
@require_permission("audit", "view")
def list_logs():
    org_id = resolve_org_id()
    limit = int(request.args.get("limit") or 200)
    limit = max(1, min(limit, 2000))

    logs = (
        AuditLog.query.filter_by(org_id=org_id)
        .order_by(AuditLog.id.desc())
        .limit(limit)
        .all()
    )
    return jsonify([l.to_dict() for l in logs]), HTTPStatus.OK


@bp.get("/logs/<int:log_id>")
@require_permission("audit", "view")
def get_log(log_id: int):
    org_id = resolve_org_id()
    log = AuditLog.query.filter_by(org_id=org_id, id=log_id).first()
    if log is None:
        return jsonify({"error": "not_found"}), HTTPStatus.NOT_FOUND
    return jsonify(log.to_dict()), HTTPStatus.OK


@bp.post("/export")
@require_permission("audit", "export")
def export_logs():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    result = export_audit_logs(org_id, payload)
    return jsonify(result), HTTPStatus.OK
