from datetime import UTC, datetime, timedelta

from erp import db
from erp.models import BotJobOutbox, MaintenanceEscalationEvent, MaintenanceWorkOrder


def _seed_ops_data(org_id: int) -> None:
    now = datetime.now(UTC)
    BotJobOutbox.query.delete()
    MaintenanceEscalationEvent.query.delete()
    MaintenanceWorkOrder.query.delete()
    db.session.add_all(
        [
            MaintenanceWorkOrder(
                org_id=org_id,
                title="Recent WO",
                description="healthy",
                status="open",
                last_check_in_at=now - timedelta(hours=1),
                sla_status="ok",
            ),
            MaintenanceWorkOrder(
                org_id=org_id,
                title="Stale WO",
                description="needs check-in",
                status="open",
                last_check_in_at=now - timedelta(hours=48),
                sla_status="breach",
            ),
        ]
    )
    db.session.add_all(
        [
            MaintenanceEscalationEvent(org_id=org_id, status="triggered"),
            MaintenanceEscalationEvent(org_id=org_id, status="resolved"),
        ]
    )
    db.session.add_all(
        [
            BotJobOutbox(
                org_id=org_id,
                bot_name="ops",
                chat_id="123",
                message_id="msg-queued",
                status="queued",
            ),
            BotJobOutbox(
                org_id=org_id,
                bot_name="ops",
                chat_id="123",
                message_id="msg-failed",
                status="failed",
            ),
            BotJobOutbox(
                org_id=org_id,
                bot_name="ops",
                chat_id="123",
                message_id="msg-completed",
                status="completed",
            ),
        ]
    )
    db.session.commit()


def test_operations_summary_counts(app, client):
    app.config.update(LOGIN_DISABLED=True)
    with app.app_context():
        _seed_ops_data(org_id=1)

    res = client.get("/api/analytics-dash/operations?hours=24")
    assert res.status_code == 200
    payload = res.get_json()
    assert payload["maintenance_escalations"]["open"] == 1
    assert payload["maintenance_escalations"]["resolved"] == 1
    assert payload["maintenance_escalations"]["total"] == 2
    assert payload["geo_offline"]["stale_work_orders"] == 1
    assert payload["geo_offline"]["recent_checkins"] == 1
    assert payload["sla"]["at_risk"] == 1
    assert payload["geo_offline"]["lookback_hours"] == 24


def test_operations_summary_invalid_hours(app, client):
    res = client.get("/api/analytics-dash/operations?hours=0")
    assert res.status_code == 400
    assert res.get_json()["error"] == "invalid_hours"


def test_bot_activity_rollup(app, client):
    app.config.update(LOGIN_DISABLED=True)
    with app.app_context():
        _seed_ops_data(org_id=1)

    res = client.get("/api/analytics-dash/bot-activity")
    assert res.status_code == 200
    payload = res.get_json()
    assert payload["total"] == 3
    assert payload["queued"] == 1
    assert payload["failed"] == 1
    assert payload["successful"] == 1


def test_executive_summary_rollup(app, client):
    app.config.update(LOGIN_DISABLED=True)
    with app.app_context():
        _seed_ops_data(org_id=1)
        # Seed minimal order and procurement data
        from erp.models import Order
        from erp.procurement.models import ProcurementTicket

        db.session.add(
            Order(organization_id=1, status="approved", total_amount=1000, commission_status="eligible")
        )
        db.session.add(
            Order(organization_id=1, status="submitted", total_amount=500, commission_status="blocked")
        )
        db.session.add(
            ProcurementTicket(organization_id=1, title="PO", description="desc", status="submitted")
        )
        db.session.commit()

    res = client.get("/api/analytics-dash/executive")
    assert res.status_code == 200
    payload = res.get_json()
    assert payload["orders"]["total"] == 2
    assert payload["orders"]["approved"] == 1
    assert payload["orders"]["pending"] == 1
    assert payload["orders"]["commission"]["eligible"] == 1
    assert payload["orders"]["commission"]["blocked"] == 1
    assert payload["procurement"]["total"] == 1
    assert payload["maintenance"]["open"] >= 0
