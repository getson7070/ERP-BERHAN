import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))  # noqa: E402

from erp import create_app  # noqa: E402
from db import get_db  # noqa: E402


def test_token_rate_limit(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "rl.db"))
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    conn = get_db()
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT,
            mfa_secret TEXT,
            approved_by_ceo BOOLEAN DEFAULT TRUE
        )
        """
    )
    conn.commit()
    conn.close()

    payload = {"email": "u@example.com", "password": "pw"}
    assert client.post("/auth/token", json=payload).status_code == 401
    resp = client.post("/auth/token", json=payload)
    assert resp.status_code == 429
    metrics = client.get("/metrics")
    assert b"rate_limit_rejections_total 1.0" in metrics.data
