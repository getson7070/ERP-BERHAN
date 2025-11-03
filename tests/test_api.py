import json
import hmac
import hashlib
import pathlib
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app, GRAPHQL_REJECTS
from db import get_db


def setup_db(tmp_path, monkeypatch):
    db_file = tmp_path / "api.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    conn = get_db()
    conn.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER, quantity INTEGER, customer TEXT, status TEXT)"
    )
    conn.execute(
        "INSERT INTO orders (item_id, quantity, customer, status) VALUES (1, 2, 'Alice', 'pending')"
    )
    conn.execute(
        "CREATE TABLE tenders (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, workflow_state TEXT)"
    )
    conn.execute(
        "INSERT INTO tenders (description, workflow_state) VALUES ('Tender A', 'advert_registered')"
    )
    conn.commit()
    conn.close()


def test_rest_and_graphql(tmp_path, monkeypatch):
    monkeypatch.setenv("API_TOKEN", "testtoken")
    setup_db(tmp_path, monkeypatch)
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    resp = client.get("/api/orders", headers={"Authorization": "Bearer testtoken"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data[0]["customer"] == "Alice"

    resp = client.get("/api/tenders", headers={"Authorization": "Bearer testtoken"})
    assert resp.status_code == 200
    assert resp.get_json()[0]["description"] == "Tender A"

    query = "{ orders { customer quantity } tenders { description } compliance { tendersDue } }"
    resp = client.post(
        "/api/graphql",
        json={"query": query},
        headers={"Authorization": "Bearer testtoken"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["orders"][0]["customer"] == "Alice"
    assert body["tenders"][0]["description"] == "Tender A"
    assert "tendersDue" in body["compliance"]


def test_webhook_requires_token(monkeypatch, tmp_path):
    monkeypatch.setenv("API_TOKEN", "webhooktoken")
    setup_db(tmp_path, monkeypatch)
    app = create_app()
    app.config["TESTING"] = True
    app.config["WEBHOOK_SECRET"] = "secret"
    client = app.test_client()

    payload = b'{"a":1}'
    sig = hmac.new(b"secret", payload, hashlib.sha256).hexdigest()
    resp = client.post(
        "/api/webhook/source",
        data=payload,
        headers={"X-Signature": sig, "Content-Type": "application/json"},
    )
    assert resp.status_code == 401
    resp = client.post(
        "/api/webhook/source",
        data=payload,
        headers={
            "Authorization": "Bearer webhooktoken",
            "X-Signature": sig,
            "Content-Type": "application/json",
            "Idempotency-Key": "key123",
        },
    )
    assert resp.status_code == 200


def test_graphql_depth_limit(monkeypatch, tmp_path):
    GRAPHQL_REJECTS._value.set(0)  # reset counter for isolated testing
    monkeypatch.setenv("API_TOKEN", "limit")
    setup_db(tmp_path, monkeypatch)
    app = create_app()
    app.config["TESTING"] = True
    app.config["GRAPHQL_MAX_DEPTH"] = 2
    client = app.test_client()
    deep_query = "{ __schema { types { fields { name } } } }"
    resp = client.post(
        "/api/graphql",
        json={"query": deep_query},
        headers={"Authorization": "Bearer limit"},
    )
    assert resp.status_code == 400
    with open(
        pathlib.Path(__file__).parent / "snapshots" / "graphql_depth_error.json"
    ) as f:
        expected = json.load(f)
    assert resp.get_json() == expected
    metrics = client.get("/metrics")
    assert b"graphql_rejects_total 1.0" in metrics.data


def test_graphql_complexity_limit(monkeypatch, tmp_path):
    GRAPHQL_REJECTS._value.set(0)
    monkeypatch.setenv("API_TOKEN", "limit")
    setup_db(tmp_path, monkeypatch)
    app = create_app()
    app.config["TESTING"] = True
    app.config["GRAPHQL_MAX_COMPLEXITY"] = 5
    client = app.test_client()
    complex_query = (
        "{ " + " ".join([f"a{i}: orders {{ id }}" for i in range(10)]) + " }"
    )
    resp = client.post(
        "/api/graphql",
        json={"query": complex_query},
        headers={"Authorization": "Bearer limit"},
    )
    assert resp.status_code == 400
    with open(
        pathlib.Path(__file__).parent / "snapshots" / "graphql_complexity_error.json"
    ) as f:
        expected = json.load(f)
    assert resp.get_json() == expected
    metrics = client.get("/metrics")
    assert b"graphql_rejects_total 1.0" in metrics.data


