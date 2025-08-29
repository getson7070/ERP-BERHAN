
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
    monkeypatch.setattr(update_status.analytics, "kpi_staleness_seconds", lambda: 5.0)

    class DummyRedis:
        def llen(self, name):
            return 3

    monkeypatch.setattr(update_status, "redis_client", DummyRedis())
    update_status.write_status(path)
    content = path.read_text()
    assert "5s" in content and "3" in content
