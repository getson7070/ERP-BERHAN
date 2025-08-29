from erp import create_app, QUEUE_LAG
from db import redis_client
from scripts import update_status


def test_queue_lag_metric(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'test.db'}")
    app = create_app()
    with app.app_context():
        redis_client.delete("celery")
        redis_client.rpush("celery", "task1")
        client = app.test_client()
        client.get("/metrics")
        assert QUEUE_LAG.labels("celery")._value.get() == 1
        redis_client.delete("celery")


def test_update_status(tmp_path, monkeypatch):
    path = tmp_path / "status.md"
    monkeypatch.setattr(
        update_status,
        "fetch_metrics",
        lambda: {
            "p95_latency_ms": 7,
            "mv_age_s": 5,
            "queue_lag": 3,
            "rate_limit_429s": 1,
        },
    )
    monkeypatch.setattr(update_status, "fetch_audit_run_id", lambda: "99")
    update_status.write_status(path)
    content = path.read_text()
    assert all(x in content for x in ["7ms", "5s", "3", "1", "run 99"])
