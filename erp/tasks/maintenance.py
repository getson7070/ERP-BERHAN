"""Celery tasks for preventive maintenance generation and escalations."""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from celery import shared_task

from erp.extensions import db
from erp.models import (
    FinanceAuditLog,
    MaintenanceAsset,
    MaintenanceEscalationEvent,
    MaintenanceEscalationRule,
    MaintenanceEvent,
    MaintenanceSchedule,
    MaintenanceWorkOrder,
)


@shared_task(name="erp.tasks.maintenance.generate_scheduled_work_orders")
def generate_scheduled_work_orders() -> None:
    """Create preventive work orders for schedules that are due."""

    today = date.today()
    schedules = (
        MaintenanceSchedule.query.filter(
            MaintenanceSchedule.is_active.is_(True),
            MaintenanceSchedule.schedule_type == "time",
            MaintenanceSchedule.next_due_date <= today,
        )
        .options()
        .all()
    )

    created_count = 0
    for schedule in schedules:
        existing = MaintenanceWorkOrder.query.filter(
            MaintenanceWorkOrder.org_id == schedule.org_id,
            MaintenanceWorkOrder.schedule_id == schedule.id,
            MaintenanceWorkOrder.status.in_(["open", "in_progress"]),
        ).first()
        if existing:
            continue

        work_order = MaintenanceWorkOrder(
            org_id=schedule.org_id,
            asset_id=schedule.asset_id,
            schedule_id=schedule.id,
            work_type="preventive",
            title=f"PM: {schedule.name}",
            description=f"Preventive maintenance for {schedule.name}",
            status="open",
            priority="normal",
            requested_at=datetime.now(UTC),
            due_date=schedule.next_due_date,
        )
        db.session.add(work_order)

        event = MaintenanceEvent(
            org_id=schedule.org_id,
            work_order=work_order,
            event_type="STATUS_CHANGE",
            from_status=None,
            to_status="open",
        )
        db.session.add(event)

        if schedule.interval_days:
            schedule.last_completed_date = schedule.next_due_date
            schedule.next_due_date = schedule.next_due_date + timedelta(days=schedule.interval_days)

        created_count += 1

    if created_count:
        db.session.commit()
    else:
        db.session.flush()


@shared_task(name="erp.tasks.maintenance.check_escalations")
def check_escalations() -> None:
    """Trigger escalation events for overdue downtime on critical assets."""

    now = datetime.now(UTC)
    work_orders = MaintenanceWorkOrder.query.filter(
        MaintenanceWorkOrder.status.in_(["open", "in_progress"]),
        MaintenanceWorkOrder.downtime_start.isnot(None),
    ).all()
    if not work_orders:
        return

    rules = MaintenanceEscalationRule.query.filter(
        MaintenanceEscalationRule.is_active.is_(True)
    ).all()
    if not rules:
        return

    for work_order in work_orders:
        asset = work_order.asset
        if not asset or not asset.is_critical:
            continue

        elapsed = now - work_order.downtime_start
        elapsed_minutes = int(elapsed.total_seconds() // 60)

        for rule in rules:
            if rule.org_id != work_order.org_id:
                continue
            if rule.asset_id and rule.asset_id != asset.id:
                continue
            if rule.asset_category and rule.asset_category != asset.category:
                continue
            if elapsed_minutes < rule.downtime_threshold_minutes:
                continue

            exists = MaintenanceEscalationEvent.query.filter_by(
                org_id=work_order.org_id, rule_id=rule.id, work_order_id=work_order.id
            ).first()
            if exists:
                continue

            escalation = MaintenanceEscalationEvent(
                org_id=work_order.org_id,
                rule_id=rule.id,
                work_order_id=work_order.id,
                status="triggered",
            )
            db.session.add(escalation)

            event = MaintenanceEvent(
                org_id=work_order.org_id,
                work_order=work_order,
                event_type="ESCALATION_TRIGGERED",
                message=f"Escalation rule {rule.name} triggered after {elapsed_minutes} minutes",
            )
            db.session.add(event)

            audit = FinanceAuditLog(
                org_id=work_order.org_id,
                event_type="MAINTENANCE_ESCALATION",
                entity_type="MAINTENANCE_WORK_ORDER",
                entity_id=work_order.id,
                payload={"rule": rule.name, "elapsed_minutes": elapsed_minutes},
            )
            db.session.add(audit)

    db.session.commit()
