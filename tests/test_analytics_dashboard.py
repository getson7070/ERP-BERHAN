def test_analytics_dashboard_html(client):
    rv = client.get("/analytics/")
    assert rv.status_code == 200
    assert b"Operational Pulse" in rv.data


def test_analytics_dashboard_json(client):
    rv = client.get("/analytics/dashboard?format=json", headers={"Accept": "application/json"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert "pending_orders" in data
    assert "monthly_sales" in data
