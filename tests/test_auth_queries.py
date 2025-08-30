from pathlib import Path
from sqlalchemy import text
import pyotp
from erp import create_app
from db import get_db
from erp.utils import hash_password
from erp.routes import auth as auth_module


def test_auth_queries_parameterised():
    content = Path("erp/routes/auth.py").read_text()
    assert "?" not in content
    assert "text(" in content


def test_issue_token(tmp_path, monkeypatch):
    db_file = tmp_path / "auth.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    app = create_app()
    with app.app_context():
        conn = get_db()
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.execute(
            text(
                "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, password_hash TEXT, mfa_secret TEXT, role TEXT, permissions TEXT, approved_by_ceo BOOLEAN, user_type TEXT, org_id INTEGER)"
            )
        )
        password_hash = hash_password("pw")
        secret = pyotp.random_base32()
        conn.execute(
            text(
                "INSERT INTO users (email, password_hash, mfa_secret, role, permissions, approved_by_ceo, user_type, org_id) VALUES ('u@example.com', :ph, :secret, 'Management', '', 1, 'employee', 1)"
            ),
            {"ph": password_hash, "secret": secret},
        )
        conn.commit()
        monkeypatch.setattr(auth_module, "_check_backoff", lambda email: ("ok", 0))
        monkeypatch.setattr(auth_module, "_record_failure", lambda *a, **k: None)
        monkeypatch.setattr(auth_module, "_clear_failures", lambda *a, **k: None)
        app.config["WTF_CSRF_ENABLED"] = False
        client = app.test_client()
        resp = client.post(
            "/auth/token",
            json={
                "email": "u@example.com",
                "password": "pw",
                "totp": pyotp.TOTP(secret).now(),
            },
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json
