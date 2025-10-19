import erp.routes.health as health
from erp import create_app


def test_healthz_reports_failure(monkeypatch):
    app = create_app()
    client = app.test_client()
    monkeypatch.setattr(health, "_ping_db", lambda: False)
    monkeypatch.setattr(health, "_ping_redis", lambda: False)
    resp = client.get("/healthz")
    assert resp.status_code == 503


