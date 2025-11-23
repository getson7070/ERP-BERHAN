import pytest


def _auth_headers(user):
    return {}


@pytest.fixture
def crm_user(make_user_with_role):
    return make_user_with_role("crm")


def test_pipeline_advances_in_order(client, db_session, crm_user):
    headers = _auth_headers(crm_user)

    resp = client.post(
        "/api/crm/accounts",
        json={"name": "Tikur Anbessa Hospital", "pipeline_stage": "lead", "segment": "A"},
        headers=headers,
    )
    assert resp.status_code == 201
    account = resp.get_json()
    account_id = account["id"]
    assert account["pipeline_stage"] == "lead"

    resp = client.post(
        f"/api/crm/accounts/{account_id}/advance-stage",
        json={"reason": "Qualified interest"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["account"]["pipeline_stage"] == "prospect"

    resp = client.post(
        f"/api/crm/accounts/{account_id}/advance-stage",
        json={"reason": "Signed contract"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["account"]["pipeline_stage"] == "client"

    resp = client.post(
        f"/api/crm/accounts/{account_id}/advance-stage",
        json={"reason": "extra"},
        headers=headers,
    )
    assert resp.status_code == 400


def test_non_crm_user_cannot_advance_stage(client, db_session, make_user_with_role):
    crm_user = make_user_with_role("crm")
    headers_crm = _auth_headers(crm_user)

    resp = client.post(
        "/api/crm/accounts",
        json={"name": "Shashemene General Hospital"},
        headers=headers_crm,
    )
    assert resp.status_code == 201
    account_id = resp.get_json()["id"]

    staff_user = make_user_with_role("staff")
    headers_staff = _auth_headers(staff_user)

    resp = client.post(
        f"/api/crm/accounts/{account_id}/advance-stage",
        json={"reason": "attempt"},
        headers=headers_staff,
    )
    assert resp.status_code in (401, 403)
