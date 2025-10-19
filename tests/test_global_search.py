import os
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from erp import create_app
from db import get_db


def setup_db(tmp_path):
    db_file = tmp_path / "search.db"
    os.environ["DATABASE_PATH"] = str(db_file)
    conn = get_db()
    conn.execute(
        "CREATE TABLE crm_customers (id INTEGER PRIMARY KEY AUTOINCREMENT, org_id INTEGER, name TEXT)"
    )
    conn.execute(
        "CREATE TABLE inventory_items (id INTEGER PRIMARY KEY AUTOINCREMENT, org_id INTEGER, name TEXT, sku TEXT UNIQUE, quantity INTEGER)"
    )
    conn.execute(
        "CREATE TABLE hr_employees (id INTEGER PRIMARY KEY AUTOINCREMENT, org_id INTEGER, name TEXT)"
    )
    conn.execute(
        "CREATE TABLE finance_transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, org_id INTEGER, description TEXT)"
    )
    conn.execute("INSERT INTO crm_customers (org_id, name) VALUES (1, 'Alice Co')")
    conn.execute(
        "INSERT INTO inventory_items (org_id, name, sku, quantity) VALUES (1, 'Widget', 'W-1', 5)"
    )
    conn.execute("INSERT INTO hr_employees (org_id, name) VALUES (1, 'Bob')")
    conn.execute(
        "INSERT INTO finance_transactions (org_id, description) VALUES (1, 'Consulting Fee')"
    )
    conn.commit()
    conn.close()


def test_global_search_returns_results(tmp_path):
    setup_db(tmp_path)
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["role"] = "Employee"
        sess["org_id"] = 1
        sess["user_id"] = 1
    res = client.get("/search?q=Alice")
    text = res.get_data(as_text=True)
    assert "Alice Co" in text
    assert "CRM" in text


