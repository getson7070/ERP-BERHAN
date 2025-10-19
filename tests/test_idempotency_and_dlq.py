import json
from types import SimpleNamespace
import sys
from pathlib import Path
import hmac
import hashlib

import pytest
from flask import Blueprint

sys.path.append(str(Path(__file__).resolve().parents[1]))

from erp import create_app, _dead_letter_handler
from erp.utils import idempotency_key_required
from db import redis_client


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = False
    app.config["API_TOKEN"] = "test-token"
    app.config["WEBHOOK_SECRET"] = "secret"

    bp = Blueprint("test_idem", __name__)

    @bp.route("/idem", methods=["POST"])
    @idempotency_key_required
    def idem_endpoint():
        return "", 200

    app.register_blueprint(bp)
    return app.test_client()


def test_idempotency_decorator_blocks_duplicates(client):
    headers = {"Idempotency-Key": "abc"}
    assert client.post("/idem", headers=headers).status_code == 200
    assert client.post("/idem", headers=headers).status_code == 409


def test_dead_letter_queue_records_failures():
    redis_client.delete("dead_letter")
    dummy = SimpleNamespace(name="erp.tasks.example")
    _dead_letter_handler(
        sender=dummy,
        task_id="42",
        exception=Exception("boom"),
        args=(1,),
        kwargs={"a": 2},
    )
    entries = redis_client.lrange("dead_letter", 0, -1)
    assert entries, "dead-letter queue should capture failed task"
    payload = json.loads(entries[0])
    assert payload["task"] == "erp.tasks.example"
    assert payload["id"] == "42"


def test_webhook_failure_queues_dead_letter(client):
    redis_client.delete("dead_letter")
    payload = {"simulate_failure": True}
    body = json.dumps(payload)
    sig = hmac.new(b"secret", body.encode(), hashlib.sha256).hexdigest()
    resp = client.post(
        "/api/webhook/test",
        data=body,
        headers={
            "Authorization": "Bearer test-token",
            "Idempotency-Key": "abc",
            "X-Signature": sig,
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 500
    entries = redis_client.lrange("dead_letter", 0, -1)
    assert entries, "webhook failures should enter dead-letter queue"


