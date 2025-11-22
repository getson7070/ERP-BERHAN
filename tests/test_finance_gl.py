from decimal import Decimal
import datetime as dt
import pytest


def _auth_headers(user):
    return {}


@pytest.fixture
def finance_user(make_user_with_role):
    return make_user_with_role("finance")


def test_cannot_create_unbalanced_journal(client, db_session, finance_user):
    headers = _auth_headers(finance_user)
    today = dt.date.today().isoformat()

    resp = client.post(
        "/api/finance/journal",
        json={
            "document_date": today,
            "posting_date": today,
            "currency": "ETB",
            "fx_rate": "1",
            "lines": [
                {"account_code": "1000", "debit": 100, "credit": 0},
                {"account_code": "2000", "debit": 0, "credit": 50},
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 400
    assert "Unbalanced" in resp.get_json()["error"]


def test_can_post_balanced_multi_currency_journal(client, db_session, finance_user):
    headers = _auth_headers(finance_user)
    today = dt.date.today().isoformat()

    resp = client.post(
        "/api/finance/journal",
        json={
            "document_date": today,
            "posting_date": today,
            "currency": "USD",
            "base_currency": "ETB",
            "fx_rate": "50",
            "lines": [
                {"account_code": "1000", "debit": 100, "credit": 0},
                {"account_code": "2000", "debit": 0, "credit": 100},
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    entry = resp.get_json()
    entry_id = entry["id"]

    resp = client.post(f"/api/finance/journal/{entry_id}/post", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "posted"
    assert data["currency"] == "USD"
    for line in data["lines"]:
        assert line["debit_base"] in (0.0, 5000.0)
        assert line["credit_base"] in (0.0, 5000.0)
