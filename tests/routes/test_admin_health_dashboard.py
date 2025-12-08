import os

from erp import create_app


def test_admin_health_dashboard_json(monkeypatch):
    # Keep the health registry happy without production secrets during tests.
    monkeypatch.setenv("ALLOW_INSECURE_DEFAULTS", "1")
    monkeypatch.setenv("SECRET_KEY", "test-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///health.db")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt")

    app = create_app()
    app.config["LOGIN_DISABLED"] = True

    client = app.test_client()
    resp = client.get(
        "/admin/health?format=json",
        headers={"Accept": "application/json"},
    )

    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["status"] in ("ok", "error")
    assert isinstance(payload.get("checks"), dict)
    # Ensure critical health gates are present when rendered via JSON.
    assert "config" in payload["checks"]
    assert "db_migrations" in payload["checks"]
