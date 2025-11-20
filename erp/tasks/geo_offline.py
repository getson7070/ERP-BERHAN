"""Offline detection for field staff and drivers."""
from __future__ import annotations

from datetime import datetime, timedelta

from celery import shared_task

from erp.extensions import db
from erp.models import FinanceAuditLog, GeoAssignment, GeoLastLocation, MarketingEvent


@shared_task(name="erp.tasks.geo.check_offline_subjects")
def check_offline_subjects(minutes: int = 30):
    """Raise an alert when an active assignment stops reporting location pings."""

    cutoff = datetime.utcnow() - timedelta(minutes=minutes)

    active_assignments = GeoAssignment.query.filter_by(status="active").all()
    for assignment in active_assignments:
        last = GeoLastLocation.query.filter_by(
            org_id=assignment.org_id,
            subject_type=assignment.subject_type,
            subject_id=assignment.subject_id,
        ).first()
        if not last or last.updated_at < cutoff:
            db.session.add(
                FinanceAuditLog(
                    org_id=assignment.org_id,
                    event_type="GEO_OFFLINE_ALERT",
                    entity_type=assignment.task_type.upper(),
                    entity_id=assignment.task_id,
                    payload={
                        "subject_type": assignment.subject_type,
                        "subject_id": assignment.subject_id,
                        "last_seen": last.updated_at.isoformat() if last else None,
                        "threshold_minutes": minutes,
                    },
                )
            )
            db.session.add(
                MarketingEvent(
                    org_id=assignment.org_id,
                    campaign_id=0,
                    subject_type=assignment.subject_type,
                    subject_id=assignment.subject_id,
                    event_type="geo_offline_alert",
                    metadata_json={"task_type": assignment.task_type, "task_id": assignment.task_id},
                )
            )

    db.session.commit()
