from erp import create_app


def test_collect_vitals_schema(monkeypatch):
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    app = create_app()
    client = app.test_client()
    resp = client.post("/analytics/vitals", json={"bad": "value"})
    assert resp.status_code == 400
    resp = client.post("/analytics/vitals", json={"lcp": 1.1})
    assert resp.status_code == 204


