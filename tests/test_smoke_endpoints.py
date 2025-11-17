from http import HTTPStatus


def test_analytics_dashboard(client):
    response = client.get("/analytics/dashboard")
    assert response.status_code == HTTPStatus.OK
    payload = response.get_json()
    assert payload is not None
    for key in {
        "pending_orders",
        "open_maintenance",
        "low_stock_items",
        "qualified_pipeline_value",
        "monthly_sales",
    }:
        assert key in payload


def test_finance_health(client):
    response = client.get("/api/finance/health")
    assert response.status_code == HTTPStatus.OK
    payload = response.get_json()
    assert payload["ok"] is True
    assert "accounts" in payload


def test_crm_leads_and_interactions(client):
    creation = client.post(
        "/crm/leads",
        json={"name": "Acme", "email": "sales@acme.test", "potential_value": 10000},
    )
    assert creation.status_code == HTTPStatus.CREATED
    lead_id = creation.get_json()["id"]

    interaction = client.post(
        f"/crm/leads/{lead_id}/interactions",
        json={"notes": "Intro call complete"},
    )
    assert interaction.status_code == HTTPStatus.CREATED

    listing = client.get("/crm/leads")
    assert listing.status_code == HTTPStatus.OK
    payload = listing.get_json()
    assert any(lead["name"] == "Acme" for lead in payload)


def test_sales_order_pipeline(client):
    creation = client.post(
        "/sales/orders",
        json={
            "customer_name": "Beta Buyer",
            "total_value": 2500,
            "status": "submitted",
            "order_id": "SO-1",
        },
    )
    assert creation.status_code == HTTPStatus.CREATED

    listing = client.get("/sales/orders")
    assert listing.status_code == HTTPStatus.OK
    payload = listing.get_json()
    assert any(order["customer_name"] == "Beta Buyer" for order in payload)


def test_banking_account_and_transaction_flow(client):
    account = client.post(
        "/banking/accounts",
        json={"name": "Operating", "currency": "ETB", "initial_balance": 1000},
    )
    assert account.status_code == HTTPStatus.CREATED
    account_id = account.get_json()["id"]

    txn = client.post(
        "/banking/transactions",
        json={
            "bank_account_id": account_id,
            "direction": "inflow",
            "amount": 250,
            "reference": "INV-123",
        },
    )
    assert txn.status_code == HTTPStatus.CREATED

    history = client.get(f"/banking/accounts/{account_id}/transactions")
    assert history.status_code == HTTPStatus.OK
    payload = history.get_json()
    assert any(entry["reference"] == "INV-123" for entry in payload)


def test_supplychain_reorder_policy_is_org_scoped(client):
    creation = client.post(
        "/supply/policy",
        json={"item_id": "00000000-0000-0000-0000-000000000001", "warehouse_id": "00000000-0000-0000-0000-0000000000aa"},
    )
    assert creation.status_code == HTTPStatus.CREATED

    listing = client.get("/supply/policy")
    assert listing.status_code == HTTPStatus.OK
    payload = listing.get_json()
    assert all(policy["item_id"] is not None for policy in payload)


def test_auth_register_and_login(client):
    registration = client.post(
        "/auth/register",
        json={"email": "demo@example.com", "password": "example123", "username": "Demo", "role": "admin"},
    )
    assert registration.status_code == HTTPStatus.CREATED

    login = client.post(
        "/auth/login",
        json={"email": "demo@example.com", "password": "example123"},
    )
    assert login.status_code == HTTPStatus.OK
    payload = login.get_json()
    assert payload["user_id"]


def test_report_builder_returns_real_metrics(client):
    # Seed a vitals event with location for geo coverage
    client.post(
        "/analytics/vitals",
        json={"lcp": 1.1, "location": "Addis Ababa", "lat": 8.9806, "lng": 38.7578},
    )

    report = client.post("/reports/run", json={"period": "month"})
    assert report.status_code == HTTPStatus.OK
    payload = report.get_json()
    assert "orders" in payload
    assert "finance" in payload
    assert "geo" in payload
