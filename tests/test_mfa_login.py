from http import HTTPStatus

import pyotp

from erp import db
from erp.models import User
from erp.services.mfa_service import enable_mfa, generate_totp_secret


def test_mfa_blocks_plain_login(app, client):
    app.config["LOGIN_DISABLED"] = False
    with app.app_context():
        user = User(username="alice", email="alice@example.com")
        user.password = "SecretPass123"
        db.session.add(user)
        db.session.commit()

        secret = generate_totp_secret()
        enable_mfa(1, user.id, secret)

    resp = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "SecretPass123"},
    )
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    assert "mfa_required" in resp.get_json().get("error", "")

    valid_code = pyotp.TOTP(secret).now()
    resp_ok = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "SecretPass123", "totp": valid_code},
    )
    assert resp_ok.status_code == HTTPStatus.OK
