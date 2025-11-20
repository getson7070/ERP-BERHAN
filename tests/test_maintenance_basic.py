import datetime as dt

import pytest


def _auth_headers(user):
    return {}


@pytest.fixture
def maintenance_user(make_user_with_role):
    return make_user_with_role("maintenance")


def test_preventive_schedule_creates_work_order(client, db_session, maintenance_user, resolve_org_id):
    from erp.models import MaintenanceAsset, MaintenanceSchedule, MaintenanceWorkOrder
    from erp.tasks.maintenance import generate_scheduled_work_orders

    org_id = resolve_org_id()

    asset = MaintenanceAsset(
        org_id=org_id,
        code="EXC200-001",
        name="Zybio EXC200 Chemistry Analyzer",
        is_critical=True,
    )
    db_session.add(asset)
    db_session.flush()

    schedule = MaintenanceSchedule(
        org_id=org_id,
        asset_id=asset.id,
        name="Monthly Preventive Maintenance",
        schedule_type="time",
        interval_days=30,
        next_due_date=dt.date.today(),
        is_active=True,
    )
    db_session.add(schedule)
    db_session.commit()

    generate_scheduled_work_orders()

    work_orders = MaintenanceWorkOrder.query.filter_by(org_id=org_id, schedule_id=schedule.id).all()
    assert len(work_orders) == 1
    assert work_orders[0].work_type == "preventive"
    assert work_orders[0].status == "open"


def test_escalation_rule_creation_and_trigger(client, db_session, maintenance_user, resolve_org_id):
    from erp.models import MaintenanceAsset, MaintenanceEscalationRule, MaintenanceWorkOrder
    from erp.tasks.maintenance import check_escalations

    org_id = resolve_org_id()

    asset = MaintenanceAsset(org_id=org_id, code="CRIT-001", name="Critical", is_critical=True)
    db_session.add(asset)
    db_session.flush()

    rule = MaintenanceEscalationRule(
        org_id=org_id,
        name="Escalate after 1m",
        asset_id=asset.id,
        downtime_threshold_minutes=1,
    )
    db_session.add(rule)
    db_session.flush()

    wo = MaintenanceWorkOrder(
        org_id=org_id,
        asset_id=asset.id,
        title="Repair",
        work_type="corrective",
        status="in_progress",
        requested_at=dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=5),
        downtime_start=dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=5),
    )
    db_session.add(wo)
    db_session.commit()

    check_escalations()

    db_session.refresh(wo)
    assert wo.events, "Escalation should create a work order event"
    assert any(ev.event_type == "ESCALATION_TRIGGERED" for ev in wo.events)
