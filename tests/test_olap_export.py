from pathlib import Path

from db import get_db
from scripts.olap_export import main, OLAP_EXPORT_SUCCESS


def test_olap_export_creates_csv_and_increments_metric():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS kpi_sales (org_id INTEGER, total NUMERIC)")
    cur.execute("DELETE FROM kpi_sales")
    cur.execute("INSERT INTO kpi_sales VALUES (1, 123.45)")
    conn.commit()

    before = OLAP_EXPORT_SUCCESS._value.get()
    path = main()
    assert path.exists()
    after = OLAP_EXPORT_SUCCESS._value.get()
    assert after == before + 1
    path.unlink()
    Path("exports").rmdir()


