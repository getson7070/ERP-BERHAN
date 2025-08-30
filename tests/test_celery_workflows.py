import pathlib
import sys
import math

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from erp.routes.analytics import send_approval_reminders, forecast_sales
from db import get_db


def setup_database(tmp_path, monkeypatch):
    db_file = tmp_path / "celery.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    conn = get_db()
    return conn


def test_send_approval_reminders(tmp_path, monkeypatch):
    conn = setup_database(tmp_path, monkeypatch)
    conn.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, status TEXT, sales_rep TEXT)"
    )
    conn.execute(
        "INSERT INTO orders (status, sales_rep) VALUES ('pending','rep1'), ('approved','rep2')"
    )
    conn.commit()
    count = send_approval_reminders()
    assert count == 1
    conn.close()


def test_forecast_sales(tmp_path, monkeypatch):
    conn = setup_database(tmp_path, monkeypatch)
    conn.execute("CREATE TABLE kpi_sales (month TEXT, total_sales REAL)")
    conn.execute(
        "INSERT INTO kpi_sales (month, total_sales) VALUES ('2024-01-01', 10), ('2024-02-01', 20), ('2024-03-01', 30)"
    )
    conn.commit()
    forecast = forecast_sales()
    assert math.isclose(forecast, 40.0)
    conn.close()
