from erp.services.audit_log_service import write_audit_log


def test_filter_by_module(app, client, db_session, resolve_org_id):
    org_id = resolve_org_id()
    with app.app_context():
        write_audit_log(org_id=org_id, module="inventory", action="stock.adjust", metadata={"k": "v"}, commit=True)
        write_audit_log(org_id=org_id, module="finance", action="post", metadata={}, commit=True)

    resp = client.get("/api/audit/logs?module=inventory")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["items"]
    assert all(item["module"] == "inventory" for item in body["items"])
