import pytest

from erp.models import AuditLog
from erp.services.audit_log_service import write_audit_log


def test_audit_logs_append_only_trigger(app, db_session, resolve_org_id):
    org_id = resolve_org_id()

    with app.app_context():
        entry = write_audit_log(org_id=org_id, module="test", action="create", metadata={"k": "v"}, commit=True)

    entry.action = "changed"
    failed = False
    try:
        db_session.commit()
    except Exception:
        db_session.rollback()
        failed = True
    assert failed is True


@pytest.mark.parametrize("include_payload", [False, True])
def test_audit_encryption_roundtrip(app, db_session, resolve_org_id, include_payload):
    org_id = resolve_org_id()
    payload = {"email": "someone@example.com", "note": "ok"} if include_payload else None

    with app.app_context():
        write_audit_log(
            org_id=org_id,
            module="crm",
            action="client.register",
            metadata={"client_id": 2},
            payload=payload,
            sensitive_keys={"email"},
            commit=True,
        )

    entry = AuditLog.query.filter_by(org_id=org_id, module="crm").first()
    if include_payload:
        assert entry.payload_encrypted.get("email") != "someone@example.com"
    else:
        assert entry.payload_encrypted is None
