import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from erp.routes.analytics import send_approval_reminders, forecast_sales
from db import get_db


def setup_orders(tmp_path, monkeypatch):
    db_file = tmp_path / "app.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    conn = get_db()
    conn.execute("CREATE TABLE orders (id INTEGER, sales_rep TEXT, status TEXT)")
    conn.execute(
        "INSERT INTO orders VALUES (1,'alice','pending'), (2,'bob','approved')"
    )
    conn.commit()
    return conn


def test_send_approval_reminders(tmp_path, monkeypatch):
    setup_orders(tmp_path, monkeypatch)
    count = send_approval_reminders.run()
    assert count == 1


def test_forecast_sales(tmp_path, monkeypatch):
    db_file = tmp_path / "app.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    conn = get_db()
    conn.execute("CREATE TABLE kpi_sales (month TEXT, total_sales REAL)")
    conn.execute(
        "INSERT INTO kpi_sales VALUES ('2024-01-01', 100.0), ('2024-02-01', 150.0)"
    )
    conn.commit()
    forecast = forecast_sales.run()
    assert isinstance(forecast, float)
    assert forecast > 0
