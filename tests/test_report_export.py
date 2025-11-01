import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from erp import create_app
from db import get_db


def setup_db(tmp_path, monkeypatch):
    db_file = tmp_path / "report.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    conn = get_db()
    conn.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT, status TEXT)"
    )
    conn.execute("INSERT INTO orders (customer,status) VALUES ('Bob','pending')")
    conn.execute(
        "CREATE TABLE tenders (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, status TEXT)"
    )
    conn.execute("INSERT INTO tenders (title,status) VALUES ('Bid','open')")
    conn.execute("CREATE TABLE roles (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO roles (id,name) VALUES (1,'Management')")
    conn.execute(
        "CREATE TABLE role_assignments (user_id INTEGER, role_id INTEGER, org_id INTEGER)"
    )
    conn.execute(
        "INSERT INTO role_assignments (user_id, role_id, org_id) VALUES (1,1,1)"
    )
    conn.commit()
    conn.close()


def test_report_exports(tmp_path, monkeypatch):
    setup_db(tmp_path, monkeypatch)
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["user_id"] = 1
        sess["org_id"] = 1
        sess["role"] = "Management"
    resp = client.post(
        "/analytics/reports/export/excel", data={"report_type": "orders"}
    )
    assert (
        resp.status_code == 200
        and resp.mimetype
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    resp = client.post("/analytics/reports/export/pdf", data={"report_type": "orders"})
    assert resp.status_code == 200 and resp.mimetype == "application/pdf"


