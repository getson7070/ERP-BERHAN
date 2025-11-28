from sqlalchemy import text

from erp import create_app
from erp.health import health_registry
from db import get_db


def test_health_endpoints(tmp_path, monkeypatch):
    """/health returns lightweight ok and /healthz performs deep checks."""

    db_file = tmp_path / "app.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    app = create_app()
    client = app.test_client()

    rv = client.get("/health")
    assert rv.status_code == 200
    assert rv.json["ok"] is True

    rv = client.get("/healthz")
    assert rv.status_code in (200, 503)
    if rv.status_code == 200:
        assert rv.json["ok"] is True
        assert rv.json["status"] == "ok"
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

    degraded = client.get("/healthz")
    assert degraded.status_code == 503
    degraded_payload = degraded.get_json()
    assert degraded_payload["ok"] is False
    assert degraded_payload["status"] == "error"
    assert degraded_payload["checks"]["redis"]["ok"] is False
    assert degraded_payload["checks"]["redis"]["error"] == "redis connection failed"

    with app.app_context():
        conn = get_db()
        result = conn.execute(text("SELECT 1")).scalar_one()
        assert result == 1
        conn.close()


