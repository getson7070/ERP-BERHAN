"""Lightweight activity logging helpers for cross-module analytics."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from flask_login import current_user

from erp.extensions import db
from erp.models.core_entities import ActivityEvent
from erp.utils.core import resolve_org_id

__all__ = ["log_activity_event"]


def log_activity_event(
    *,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    status: Optional[str] = None,
    severity: str = "info",
    metadata: Optional[dict[str, Any]] = None,
    actor_user_id: Optional[int] = None,
    actor_type: str | None = None,
    org_id: Optional[int] = None,
    commit: bool = False,
) -> ActivityEvent:
    """Persist a structured activity event for reporting and scorecards."""

    org_resolved = org_id or resolve_org_id()
    actor_id = actor_user_id
    if actor_id is None and getattr(current_user, "is_authenticated", False):
        actor_id = current_user.id

    event = ActivityEvent(
        org_id=org_resolved,
        actor_user_id=actor_id,
        actor_type=actor_type or ("user" if actor_id else "system"),
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        severity=severity,
        metadata=metadata or {},
        occurred_at=datetime.now(UTC),
    )
    db.session.add(event)
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return event

