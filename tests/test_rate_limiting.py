import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))  # noqa: E402

from erp import create_app  # noqa: E402
from db import get_db  # noqa: E402


def _get_rate_limit_metric(client) -> float:
    """Return the current rate_limit_rejections_total value."""
    metrics = client.get("/metrics").data.decode().splitlines()
    for line in metrics:
        if line.startswith("rate_limit_rejections_total"):
            return float(line.split()[1])
    return 0.0


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
    before = _get_rate_limit_metric(client)
    assert client.post("/auth/token", json=payload).status_code == 401
    assert client.post("/auth/token", json=payload).status_code == 401
    resp = client.post("/auth/token", json=payload)
    assert resp.status_code == 429
    after = _get_rate_limit_metric(client)
    assert after >= before + 1


def test_employee_login_rate_limit(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "rl_login.db"))
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    client = app.test_client()
    monkeypatch.setattr("erp.routes.auth.render_template", lambda *a, **k: "")

    conn = get_db()
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            user_type TEXT,
            account_locked BOOLEAN DEFAULT FALSE,
            mfa_secret TEXT,
            approved_by_ceo BOOLEAN DEFAULT TRUE,
            failed_attempts INTEGER DEFAULT 0,
            role TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    payload = {"email": "e@example.com", "password": "pw", "totp": "000000"}
    before = _get_rate_limit_metric(client)
    for _ in range(5):
        client.post("/employee_login", data=payload)
    resp = client.post("/employee_login", data=payload)
    assert resp.status_code == 429
    after = _get_rate_limit_metric(client)
    assert after >= before + 1


def test_graphql_rate_limit(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "rl_graphql.db"))
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    monkeypatch.setenv("API_TOKEN", "ratelimit")
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    query = "{ compliance { tendersDue } }"
    headers = {"Authorization": "Bearer ratelimit"}
    before = _get_rate_limit_metric(client)
    for _ in range(50):
        assert (
            client.post("/api/graphql", json={"query": query}, headers=headers).status_code
            == 200
        )
    resp = client.post("/api/graphql", json={"query": query}, headers=headers)
    assert resp.status_code == 429
    after = _get_rate_limit_metric(client)
    assert after >= before + 1
