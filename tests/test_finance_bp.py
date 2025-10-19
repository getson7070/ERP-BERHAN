def test_finance_health(client):
    rv = client.get("/finance/health")
    assert rv.status_code == 200


