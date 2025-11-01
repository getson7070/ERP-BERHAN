import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from erp import create_app
from db import get_db


def test_disabled_module_returns_403(tmp_path, monkeypatch):
    db_file = tmp_path / "wf.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    app = create_app()
    client = app.test_client()

    conn = get_db()
    conn.execute(
        "CREATE TABLE workflows (id INTEGER PRIMARY KEY AUTOINCREMENT, org_id INTEGER, module TEXT, steps TEXT, enabled BOOLEAN)"
    )
    conn.execute(
        "CREATE TABLE crm_customers (id INTEGER PRIMARY KEY AUTOINCREMENT, org_id INTEGER, name TEXT)"
    )
    conn.execute(
        "INSERT INTO workflows (org_id, module, steps, enabled) VALUES (1,'crm','[]',0)"
    )
    conn.commit()
    with client.session_transaction() as sess:
        sess["org_id"] = 1
    resp = client.get("/crm/")
    assert resp.status_code == 403


