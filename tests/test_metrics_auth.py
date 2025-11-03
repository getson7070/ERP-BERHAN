from erp import create_app


def test_metrics_requires_token(monkeypatch):
    monkeypatch.setenv("METRICS_AUTH_TOKEN", "s3cr3t")
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()
    assert client.get("/metrics").status_code == 401
    assert (
        client.get("/metrics", headers={"Authorization": "Bearer s3cr3t"}).status_code
        == 200
    )


