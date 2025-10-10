import secrets
def test_login_mfa_flow(client, db_session, user_factory):
    u = user_factory(email="mfa@example.com")
    u.set_password("Passw0rd!")
    u.enable_mfa()
    db_session.add(u); db_session.commit()

    # wrong password
    r = client.post("/auth/login", data={"email": u.email, "password": "bad"})
    assert r.status_code == 401

    # missing token
    r = client.post("/auth/login", data={"email": u.email, "password": "Passw0rd!"})
    assert r.status_code == 401

    # use recovery code
    rec = u.get_pending_recovery_codes()
    assert rec and len(rec) > 0
    r = client.post("/auth/login", data={"email": u.email, "password": "Passw0rd!", "token": rec[0]})
    assert r.status_code in (302, 303)
