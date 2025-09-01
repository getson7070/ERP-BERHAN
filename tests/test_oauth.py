import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pyotp
from sqlalchemy import text
from erp import create_app, oauth
from db import get_db
from erp.routes import auth as auth_module


def test_oauth_login_redirect(monkeypatch):
    app = create_app()
    app.config.update(
        {
            "OAUTH_CLIENT_ID": "id",
            "OAUTH_CLIENT_SECRET": "sec",
            "OAUTH_AUTH_URL": "https://sso.example/authorize",
            "OAUTH_TOKEN_URL": "https://sso.example/token",
            "OAUTH_USERINFO_URL": "https://sso.example/userinfo",
        }
    )
    oauth.register(
        "sso",
        client_id="id",
        client_secret="sec",
        access_token_url="https://sso.example/token",
        authorize_url="https://sso.example/authorize",
        client_kwargs={"scope": "openid"},
    )
    client = app.test_client()
    rv = client.get("/oauth_login")
    assert rv.status_code == 302
    assert "sso.example/authorize" in rv.location


def test_oauth_admin_requires_totp(monkeypatch, tmp_path):
    db_file = tmp_path / "auth.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    app = create_app()
    app.config.update(
        {
            "OAUTH_CLIENT_ID": "id",
            "OAUTH_CLIENT_SECRET": "sec",
            "OAUTH_AUTH_URL": "https://sso.example/authorize",
            "OAUTH_TOKEN_URL": "https://sso.example/token",
            "OAUTH_USERINFO_URL": "https://sso.example/userinfo",
        }
    )
    oauth.register(
        "sso",
        client_id="id",
        client_secret="sec",
        access_token_url="https://sso.example/token",
        authorize_url="https://sso.example/authorize",
        client_kwargs={"scope": "openid"},
    )
    app.config["WTF_CSRF_ENABLED"] = False
    with app.app_context():
        conn = get_db()
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.execute(
            text(
                "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, role TEXT, permissions TEXT, mfa_secret TEXT, approved_by_ceo BOOLEAN, user_type TEXT, org_id INTEGER, last_login TIMESTAMP)"
            )
        )
        secret = pyotp.random_base32()
        conn.execute(
            text(
                "INSERT INTO users (email, role, permissions, mfa_secret, approved_by_ceo, user_type, org_id) VALUES ('a@example.com', 'Admin', '', :sec, 1, 'employee', 1)"
            ),
            {"sec": secret},
        )
        conn.commit()
    monkeypatch.setattr(auth_module, "log_audit", lambda *a, **k: None)
    monkeypatch.setattr(oauth.sso, "authorize_access_token", lambda: {})
    class FakeResp:
        def json(self):
            return {"email": "a@example.com"}

    monkeypatch.setattr(oauth.sso, "get", lambda url, token: FakeResp())
    client = app.test_client()
    rv = client.get("/oauth_callback")
    assert rv.status_code == 302
    assert rv.location.endswith("/oauth_totp")
    code = pyotp.TOTP(secret).now()
    rv2 = client.post("/oauth_totp", data={"totp": code})
    assert rv2.status_code == 302
    with client.session_transaction() as sess:
        assert sess.get("logged_in")
