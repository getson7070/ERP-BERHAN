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
