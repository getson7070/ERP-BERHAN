import pytest


def _auth_headers(user=None):
    return {}


@pytest.fixture
def org_id(resolve_org_id):
    return resolve_org_id()


def test_client_register_and_verify(client, db_session, org_id):
    # Register
    resp = client.post(
        "/api/client-auth/register",
        json={"client_id": 10, "phone": "0912345678", "password": "StrongPass123", "method": "sms"},
    )
    assert resp.status_code == 201
    acc_id = resp.get_json()["account_id"]

    from erp.models import ClientVerification, ClientAccount

    v = ClientVerification.query.filter_by(org_id=org_id, client_account_id=acc_id).first()
    assert v is not None

    # Force known code for deterministic verify
    v.code_hash = ClientVerification.hash_code("123456")
    db_session.commit()

    resp = client.post("/api/client-auth/verify", json={"account_id": acc_id, "code": "123456"})
    assert resp.status_code == 200

    acc = ClientAccount.query.filter_by(org_id=org_id, id=acc_id).first()
    assert acc.is_verified is True
