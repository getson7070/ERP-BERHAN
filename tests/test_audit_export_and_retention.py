from datetime import UTC, datetime, timedelta

from erp.models import AuditLog
from erp.services.audit_log_service import write_audit_log
from erp.tasks.audit_retention import retention_sweep


def test_export_endpoint_returns_logs(app, client, db_session, resolve_org_id):
    org_id = resolve_org_id()
    with app.app_context():
        write_audit_log(org_id=org_id, module="finance", action="post", metadata={"ok": True}, commit=True)

    resp = client.post("/api/audit/export", json={"module": "finance"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert any(item["module"] == "finance" for item in data)


def test_retention_sweep_counts_old_logs(app, db_session, resolve_org_id):
    org_id = resolve_org_id()
    with app.app_context():
        entry = write_audit_log(org_id=org_id, module="inventory", action="adjust", metadata={}, commit=True)
        entry.created_at = datetime.now(UTC) - timedelta(days=4000)
        db_session.commit()

    result = retention_sweep(days_to_keep=3650, hard_delete=False)
    assert result["old_count"] >= 1

    still_there = AuditLog.query.filter_by(id=entry.id).first()
    assert still_there is not None
