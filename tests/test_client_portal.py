import pytest

from erp.extensions import db
from erp.models import CRMAccount, ClientPortalLink


def _auth_headers(user):
    return {}


@pytest.fixture
def portal_user_with_account(make_user, db_session, resolve_org_id):
    organization_id = resolve_org_id()
    user = make_user()

    account = CRMAccount(
        organization_id=organization_id,
        name="Portal Test Clinic",
        account_type="customer",
        pipeline_stage="client",
    )
    db.session.add(account)
    db.session.flush()

    link = ClientPortalLink(
        organization_id=organization_id,
        user_id=user.id,
        account_id=account.id,
    )
    db.session.add(link)
    db.session.commit()

    return user, account


def test_portal_user_can_see_own_account(client, portal_user_with_account):
    user, account = portal_user_with_account
    headers = _auth_headers(user)

    resp = client.get("/api/portal/me/account", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["id"] == account.id
    assert data["name"] == "Portal Test Clinic"


def test_portal_user_can_create_ticket(client, portal_user_with_account):
    user, account = portal_user_with_account
    headers = _auth_headers(user)

    resp = client.post(
        "/api/portal/me/tickets",
        json={"subject": "Analyzer down", "description": "Zybio EXC200 not starting"},
        headers=headers,
    )
    assert resp.status_code == 201
    ticket = resp.get_json()
    assert ticket["subject"] == "Analyzer down"
    assert ticket["status"] == "open"
