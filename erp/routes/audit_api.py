"""Audit log search and export endpoints."""
from __future__ import annotations

from datetime import datetime
from http import HTTPStatus
from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.models import AuditLog
from erp.security import require_roles, user_has_role
from erp.services.audit_crypto import decrypt_payload
from erp.utils import resolve_org_id

bp = Blueprint("audit_api", __name__, url_prefix="/api/audit")


def _serialize_log(entry: AuditLog, include_payload: bool = False) -> dict:
    payload = decrypt_payload(entry.payload_encrypted or {}) if include_payload else None
    return {
        "id": entry.id,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "actor_type": entry.actor_type,
        "actor_id": entry.actor_id,
        "module": entry.module,
        "action": entry.action,
        "severity": entry.severity,
        "entity_type": entry.entity_type,
        "entity_id": entry.entity_id,
        "metadata": entry.metadata_json or {},
        "ip_address": entry.ip_address,
        "request_id": entry.request_id,
        **({"payload": payload} if include_payload else {}),
    }


@bp.get("/logs")
@require_roles("admin", "compliance", "audit")
def list_logs():
    org_id = resolve_org_id()
    q = AuditLog.query.filter(AuditLog.org_id == org_id)

    args = request.args
    for field in ("module", "action", "severity", "entity_type"):
        value = args.get(field)
        if value:
            q = q.filter(getattr(AuditLog, field) == value)

    if args.get("actor_id"):
        q = q.filter(AuditLog.actor_id == int(args["actor_id"]))
    if args.get("entity_id"):
        q = q.filter(AuditLog.entity_id == int(args["entity_id"]))

    if args.get("from"):
        q = q.filter(AuditLog.created_at >= datetime.fromisoformat(args["from"]))
    if args.get("to"):
        q = q.filter(AuditLog.created_at <= datetime.fromisoformat(args["to"]))

    cursor = args.get("cursor")
    if cursor:
        q = q.filter(AuditLog.id < int(cursor))

    limit = min(int(args.get("limit", 100)), 500)
    q = q.order_by(AuditLog.id.desc()).limit(limit)
    rows = q.all()

    include_payload = user_has_role(current_user, "admin") or user_has_role(current_user, "compliance")
    next_cursor = rows[-1].id if rows else None

    return (
        jsonify(
            {
                "items": [_serialize_log(r, include_payload=include_payload) for r in rows],
                "next_cursor": next_cursor,
            }
        ),
        HTTPStatus.OK,
    )


@bp.get("/logs/<int:log_id>")
@require_roles("admin", "compliance", "audit")
def get_log(log_id: int):
    org_id = resolve_org_id()
    entry = AuditLog.query.filter_by(org_id=org_id, id=log_id).first_or_404()
    include_payload = user_has_role(current_user, "admin") or user_has_role(current_user, "compliance")
    return jsonify(_serialize_log(entry, include_payload=include_payload)), HTTPStatus.OK


@bp.post("/export")
@require_roles("admin", "compliance")
def export_logs():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    q = AuditLog.query.filter(AuditLog.org_id == org_id)
    module = payload.get("module")
    if module:
        q = q.filter(AuditLog.module == module)

    if payload.get("from"):
        q = q.filter(AuditLog.created_at >= datetime.fromisoformat(payload["from"]))
    if payload.get("to"):
        q = q.filter(AuditLog.created_at <= datetime.fromisoformat(payload["to"]))

    q = q.order_by(AuditLog.id.desc()).limit(5000)
    rows = q.all()

    include_payload = bool(payload.get("include_payload")) and (
        user_has_role(current_user, "admin") or user_has_role(current_user, "compliance")
    )

    return jsonify([_serialize_log(r, include_payload=include_payload) for r in rows]), HTTPStatus.OK
