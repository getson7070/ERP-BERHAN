def test_recall_health(client):
    rv = client.get("/recall/health")
    assert rv.status_code == 200
