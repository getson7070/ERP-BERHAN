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
