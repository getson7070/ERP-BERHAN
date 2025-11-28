from sqlalchemy import text

from erp import create_app
from erp.health import health_registry
from db import get_db


def test_health_endpoints(tmp_path, monkeypatch):
    """/health and /healthz both surface the shared registry results."""

    db_file = tmp_path / "app.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    app = create_app()
    client = app.test_client()

    rv = client.get("/health")
    assert rv.status_code in (200, 503)
    assert rv.json["status"] == ("ok" if rv.json["ok"] else "error")

    rv = client.get("/healthz")
    assert rv.status_code in (200, 503)
    assert rv.json["status"] == ("ok" if rv.json["ok"] else "error")
    if rv.status_code == 200:
        assert rv.json["checks"]["db"]["ok"] is True
        assert rv.json["checks"]["redis"]["ok"] is True

    def failing_run_all():
        return (
            False,
            {
                "redis": {
                    "ok": False,
                    "critical": True,
                    "duration_ms": 1,
                    "detail": {"message": "redis unavailable"},
                    "error": "redis connection failed",
                }
            },
        )

    monkeypatch.setattr(health_registry, "run_all", failing_run_all)

    degraded = client.get("/health")
    assert degraded.status_code == 503
    degraded_payload = degraded.get_json()
    assert degraded_payload["ok"] is False
    assert degraded_payload["status"] == "error"
    assert degraded_payload["checks"]["redis"]["ok"] is False
    assert degraded_payload["checks"]["redis"]["error"] == "redis connection failed"

    degraded_z = client.get("/healthz")
    assert degraded_z.status_code == 503
    degraded_payload_z = degraded_z.get_json()
    assert degraded_payload_z == degraded_payload

    with app.app_context():
        conn = get_db()
        result = conn.execute(text("SELECT 1")).scalar_one()
        assert result == 1
        conn.close()


def test_readyz_fails_on_critical_check(monkeypatch, tmp_path):
    """Critical check failures return 503 and mark ready=false."""

    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "app.db"))
    app = create_app()
    client = app.test_client()

    def failing_ready_checks():
        return (
            False,
            {
                "db": {"ok": False, "critical": True, "duration_ms": 1, "detail": {}, "error": "down"},
                "redis": {"ok": True, "critical": False, "duration_ms": 1, "detail": {}, "error": None},
            },
        )

    monkeypatch.setattr(health_registry, "run_all", failing_ready_checks)

    response = client.get("/readyz")
    payload = response.get_json()

    assert response.status_code == 503
    assert payload["ready"] is False
    assert payload["ok"] is False
    assert payload["status"] == "error"
    assert payload["checks"]["db"]["ok"] is False
    assert payload["checks"]["redis"]["ok"] is True


def test_readyz_succeeds_with_non_critical_failures(monkeypatch, tmp_path):
    """Non-critical failures keep the service ready while surfacing check details."""

    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "app.db"))
    app = create_app()
    client = app.test_client()

    def non_critical_failure():
        return (
            True,
            {
                "db": {"ok": True, "critical": True, "duration_ms": 1, "detail": {}, "error": None},
                "redis": {"ok": False, "critical": False, "duration_ms": 1, "detail": {}, "error": "missing"},
            },
        )

    monkeypatch.setattr(health_registry, "run_all", non_critical_failure)

    response = client.get("/readyz")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["ready"] is True
    assert payload["ok"] is True
    assert payload["status"] == "ok"
    assert payload["checks"]["redis"]["ok"] is False


def test_readyz_succeeds_when_all_critical_checks_pass(monkeypatch, tmp_path):
    """Ready endpoint returns success when all critical checks pass."""

    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "app.db"))
    app = create_app()
    client = app.test_client()

    def all_clear():
        return (
            True,
            {
                "db": {"ok": True, "critical": True, "duration_ms": 1, "detail": {}, "error": None},
                "redis": {"ok": True, "critical": False, "duration_ms": 1, "detail": {}, "error": None},
            },
        )

    monkeypatch.setattr(health_registry, "run_all", all_clear)

    response = client.get("/readyz")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["ready"] is True
    assert payload["ok"] is True
    assert payload["status"] == "ok"
    assert all(check["ok"] is True for check in payload["checks"].values())


