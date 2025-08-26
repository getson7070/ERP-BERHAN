import os
import pathlib
import os, pathlib, sys, hmac, hashlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from erp import create_app
from db import get_db


def setup_db(tmp_path, monkeypatch):
    db_file = tmp_path / "api.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    conn = get_db()
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER, quantity INTEGER, customer TEXT, status TEXT)")
    conn.execute("INSERT INTO orders (item_id, quantity, customer, status) VALUES (1, 2, 'Alice', 'pending')")
    conn.commit()
    conn.close()


def test_rest_and_graphql(tmp_path, monkeypatch):
    monkeypatch.setenv("API_TOKEN", "testtoken")
    setup_db(tmp_path, monkeypatch)
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    resp = client.get('/api/orders', headers={'Authorization': 'Bearer testtoken'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data[0]['customer'] == 'Alice'

    query = '{ orders { customer quantity } }'
    resp = client.post('/api/graphql', json={'query': query}, headers={'Authorization': 'Bearer testtoken'})
    assert resp.status_code == 200
    assert resp.get_json()['orders'][0]['customer'] == 'Alice'


def test_webhook_requires_token(monkeypatch, tmp_path):
    monkeypatch.setenv('API_TOKEN', 'webhooktoken')
    setup_db(tmp_path, monkeypatch)
    app = create_app()
    app.config['TESTING'] = True
    app.config['WEBHOOK_SECRET'] = 'secret'
    client = app.test_client()

    payload = b'{"a":1}'
    sig = hmac.new(b'secret', payload, hashlib.sha256).hexdigest()
    resp = client.post('/api/webhook/source', data=payload, headers={'X-Signature':sig,'Content-Type':'application/json'})
    assert resp.status_code == 401
    resp = client.post('/api/webhook/source', data=payload, headers={'Authorization': 'Bearer webhooktoken','X-Signature':sig,'Content-Type':'application/json'})
    assert resp.status_code == 200
