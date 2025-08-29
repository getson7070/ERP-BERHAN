from erp import create_app, QUEUE_LAG
from db import redis_client


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
