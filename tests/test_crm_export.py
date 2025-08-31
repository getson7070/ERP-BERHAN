import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))  # noqa: E402

from erp import create_app  # noqa: E402
from db import get_db  # noqa: E402


def _setup_app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "crm.db"))
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE crm_customers (id INTEGER PRIMARY KEY AUTOINCREMENT, org_id INTEGER, name TEXT)"
        )
        cur.execute(
            "CREATE TABLE workflows (org_id INTEGER, module TEXT, enabled BOOLEAN, steps TEXT)"
        )
        cur.execute(
            "INSERT INTO workflows (org_id, module, enabled, steps) VALUES (1, 'crm', 1, '[]')"
        )
        cur.execute(
            "INSERT INTO crm_customers (org_id, name) VALUES (1,'Alice'), (1,'Bob')"
        )
        conn.commit()
        cur.close()
        conn.close()
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["org_id"] = 1
    return client


def test_export_csv(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/crm/export.csv")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("text/csv")
    assert b"Alice" in resp.data


def test_export_xlsx(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/crm/export.xlsx")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith(
        "application/vnd.openxmlformats-officedocument"
    )


def test_sorting(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/crm/?sort=name&dir=desc")
    data = resp.get_json()
    assert data[0]["name"] == "Bob"


def test_invalid_sort_defaults_to_id(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/crm/?sort=bogus&dir=desc")
    data = resp.get_json()
    assert data[0]["id"] == 2


def test_invalid_direction_defaults_to_asc(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/crm/?sort=name&dir=sideways")
    data = resp.get_json()
    assert data[0]["name"] == "Alice"
