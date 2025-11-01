import pathlib
import sys
from datetime import datetime, timedelta, UTC

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from erp import create_app
from erp.routes import analytics
from db import get_db


def test_incremental_refresh_and_age_alert(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "app.db"))
    app = create_app()
    alerts: list[tuple[str, dict]] = []
    with app.app_context():
        conn = get_db()
        conn.execute("CREATE TABLE orders (order_date TEXT, total_amount REAL)")
        conn.execute(
            "CREATE TABLE kpi_sales (month TEXT PRIMARY KEY, total_sales REAL)"
        )
        conn.commit()
        monkeypatch.setattr(
            analytics.socketio, "emit", lambda e, d: alerts.append((e, d))
        )
        monkeypatch.setattr(analytics, "fetch_kpis", lambda: {})

        conn.execute(
            "INSERT INTO orders VALUES (?, ?)",
            ("2024-01-15", 100.0),
        )
        conn.commit()
        analytics.refresh_kpis.run()
        cur = conn.cursor()
        cur.execute("SELECT total_sales FROM kpi_sales WHERE month = '2024-01-01'")
        assert cur.fetchone()[0] == 100.0
        cur.close()

        conn.execute(
            "INSERT INTO orders VALUES (?, ?)",
            ("2024-02-20", 50.0),
        )
        conn.commit()
        analytics.refresh_kpis.run()
        cur = conn.cursor()
        cur.execute("SELECT SUM(total_sales) FROM kpi_sales")
        assert cur.fetchone()[0] == 150.0
        cur.close()

        old = (datetime.now(UTC) - timedelta(minutes=20)).isoformat()
        conn.execute("UPDATE kpi_refresh_log SET last_refresh = ?", (old,))
        conn.commit()
        analytics.check_kpi_staleness.run()
        assert any(
            e == "alert" and d.get("metric") == "kpi_sales_mv_age_seconds"
            for e, d in alerts
        )


