import pathlib
import sys
import time

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))  # noqa: E402

from erp import create_app  # noqa: E402
from db import get_db as real_get_db  # noqa: E402
from erp.utils import hash_password  # noqa: E402


def test_lockout_and_unlock(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "lock.db"))
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    app = create_app()
    app.config.update(TESTING=True, LOCK_THRESHOLD=2, ACCOUNT_LOCK_SECONDS=1)
    app.config["RATELIMIT_ENABLED"] = False
    from erp import limiter

    limiter.enabled = False
    client = app.test_client()

    def get_db():  # pragma: no cover - test helper
        conn = real_get_db()
        try:
            conn._raw.connection.row_factory = __import__("sqlite3").Row  # type: ignore[attr-defined]
        except Exception:
            pass
        return conn

    monkeypatch.setattr("db.get_db", get_db)
    conn = get_db()
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            password_hash TEXT,
            role TEXT,
            mfa_secret TEXT,
            approved_by_ceo BOOLEAN DEFAULT TRUE,
            org_id INTEGER,
            user_type TEXT,
            anonymized BOOLEAN DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            org_id INTEGER,
            action TEXT,
            details TEXT,
            prev_hash TEXT,
            hash TEXT,
            created_at TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO users (email, password_hash, role, mfa_secret, approved_by_ceo, org_id, user_type) VALUES (?, ?, ?, '', 1, 1, 'employee')",
        ("a@example.com", hash_password("pw"), "Employee"),
    )
    conn.commit()
    conn.close()

    payload = {"email": "a@example.com", "password": "bad"}
    for i in range(2):
        client.post("/auth/token", json=payload)
        if i == 0:
            time.sleep(2)
    resp = client.post("/auth/token", json=payload)
    assert resp.status_code == 403
    assert resp.json["error"] == "account_locked"

    time.sleep(4)
    resp = client.post("/auth/token", json={"email": "a@example.com", "password": "pw"})
    assert resp.status_code == 200
    conn = get_db()
    actions = [
        row[0] for row in conn.execute("SELECT action FROM audit_logs").fetchall()
    ]
    conn.close()
    assert "account_lock" in actions and "account_unlock" in actions
