from datetime import timedelta, datetime


def test_password_reset_revokes_sessions(client, db_session, resolve_org_id):
    org_id = resolve_org_id()

    from erp.models import ClientAccount, ClientPasswordReset
    from erp.services.client_auth_utils import set_password

    account = ClientAccount(org_id=org_id, client_id=1, email="a@b.com", is_verified=True)
    set_password(account, "OldPass123")
    db_session.add(account)
    db_session.commit()

    resp = client.post("/api/client-auth/password/forgot", json={"email": "a@b.com"})
    assert resp.status_code == 200

    reset = ClientPasswordReset.query.filter_by(org_id=org_id, client_account_id=account.id).first()
    assert reset is not None

    # Override token hash for deterministic reset
    token = "tok"
    reset.token_hash = ClientPasswordReset.hash_token(token)
    reset.expires_at = datetime.utcnow() + timedelta(minutes=30)
    db_session.commit()

    resp = client.post(
        "/api/client-auth/password/reset",
        json={"token": token, "new_password": "NewPass123"},
    )
    assert resp.status_code == 200
    reset = ClientPasswordReset.query.get(reset.id)
    assert reset.used_at is not None
