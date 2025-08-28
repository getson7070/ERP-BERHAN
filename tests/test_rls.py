import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app
from db import get_db


def setup_search_db(tmp_path, monkeypatch):
    db_file = tmp_path / "search.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    conn = get_db()
    conn.execute(
        "CREATE TABLE crm_customers (id INTEGER PRIMARY KEY AUTOINCREMENT, org_id INTEGER, name TEXT)"
    )
    conn.execute(
        "CREATE TABLE inventory_items (id INTEGER PRIMARY KEY AUTOINCREMENT, org_id INTEGER, name TEXT)"
    )
    conn.execute(
        "CREATE TABLE hr_employees (id INTEGER PRIMARY KEY AUTOINCREMENT, org_id INTEGER, name TEXT)"
    )
    conn.execute(
        "CREATE TABLE finance_transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, org_id INTEGER, description TEXT)"
    )
    conn.execute(
        "INSERT INTO crm_customers (org_id, name) VALUES (1, 'Acme'), (2, 'Other')"
    )
    conn.commit()
    conn.close()


def test_search_filters_by_org(tmp_path, monkeypatch):
    setup_search_db(tmp_path, monkeypatch)
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["org_id"] = 1
        resp = client.get("/search?q=Acme")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert "Acme" in body
        assert "Other" not in body
