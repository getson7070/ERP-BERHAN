def test_integration_health(client):
    rv = client.get("/integration/health")
    assert rv.status_code == 200


