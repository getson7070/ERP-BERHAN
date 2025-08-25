import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from erp.routes.analytics import send_order_reminders, build_report, forecast_sales
from db import get_db


def _setup_db(tmp_path, monkeypatch):
    db_file = tmp_path / "analytics.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer TEXT, quantity INTEGER, status TEXT)")
    cur.execute("CREATE TABLE audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, org_id INTEGER, action TEXT, details TEXT, created_at TIMESTAMP)")
    cur.execute("CREATE TABLE reports (id INTEGER PRIMARY KEY, institution TEXT, visit_date DATE, sales_rep TEXT)")
    cur.execute("CREATE TABLE kpi_sales (month DATE, total_sales REAL)")
    conn.commit()
    return conn


def test_send_order_reminders_writes_audit(tmp_path, monkeypatch):
    conn = _setup_db(tmp_path, monkeypatch)
    cur = conn.cursor()
    cur.execute("INSERT INTO orders (id, customer, quantity, status) VALUES (1, 'Acme', 5, 'pending')")
    conn.commit()
    send_order_reminders()
    row = conn.execute("SELECT action, details FROM audit_logs").fetchone()
    assert row == ('reminder', 'Order 1 pending approval')
    conn.close()


def test_build_report_generates_file(tmp_path, monkeypatch):
    conn = _setup_db(tmp_path, monkeypatch)
    cur = conn.cursor()
    cur.execute("INSERT INTO reports (id, institution, visit_date, sales_rep) VALUES (1, 'Inst', '2024-01-01', 'Rep')")
    conn.commit()
    filename = build_report('2024-01-01', '2024-12-31', 'visits')
    assert pathlib.Path(filename).exists()
    conn.close()


def test_forecast_sales_returns_number(tmp_path, monkeypatch):
    conn = _setup_db(tmp_path, monkeypatch)
    cur = conn.cursor()
    cur.execute("INSERT INTO kpi_sales (month, total_sales) VALUES ('2024-01-01', 10)")
    cur.execute("INSERT INTO kpi_sales (month, total_sales) VALUES ('2024-02-01', 20)")
    conn.commit()
    prediction = forecast_sales()
    assert isinstance(prediction, float)
    conn.close()
