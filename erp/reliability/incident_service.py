"""Helpers to open/close incidents for MTTR tracking."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import has_request_context

from erp.extensions import db
from erp.models import Incident
from erp.utils import resolve_org_id


def _current_org_id(fallback: int | None = 0) -> int:
    """Best-effort resolution of the current org without cross-tenant leakage.

    When no request context is available we fall back to a neutral org identifier
    (default ``0``) instead of an arbitrary tenant so incidents are not
    attributed to the wrong organisation.
    """

    if has_request_context():
        try:
            return resolve_org_id()
        except Exception:
            return fallback or 0
    return fallback or 0


def open_incident(org_id: int | None, service: str, detail: dict[str, Any] | None = None) -> Incident:
    org_val = org_id or _current_org_id()
    existing = Incident.query.filter_by(org_id=org_val, service=service, status="open").first()
    if existing:
        return existing

    incident = Incident(org_id=org_val, service=service, detail_json=detail or {})
    db.session.add(incident)
    db.session.commit()
    return incident


def close_incident(org_id: int | None, service: str) -> Incident | None:
    org_val = org_id or _current_org_id()
    incident = Incident.query.filter_by(org_id=org_val, service=service, status="open").first()
    if not incident:
        return None

    incident.status = "recovered"
    incident.recovered_at = datetime.utcnow()
    db.session.commit()
    return incident
