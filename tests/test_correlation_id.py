import os, pathlib, sys
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from erp import create_app
from db import get_db


def setup_db(tmp_path, monkeypatch):
    db_file = tmp_path/"cid.db"
    monkeypatch.setenv('DATABASE_PATH', str(db_file))
    conn = get_db()
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER, quantity INTEGER, customer TEXT, status TEXT)")
    conn.commit(); conn.close()


def test_correlation_header(tmp_path, monkeypatch):
    monkeypatch.setenv('API_TOKEN','tok')
    setup_db(tmp_path, monkeypatch)
    app = create_app(); app.config['TESTING']=True
    client = app.test_client()
    resp = client.get('/api/orders', headers={'Authorization':'Bearer tok'})
    assert 'X-Correlation-ID' in resp.headers and resp.headers['X-Correlation-ID']
