import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from erp import create_app  # noqa: E402
from sqlalchemy import text  # noqa: E402
from db import get_db  # noqa: E402


def _setup_app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "orders.db"))
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        conn = get_db()
        conn.execute(
            text(
                """
                CREATE TABLE orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER,
                    quantity INTEGER,
                    customer TEXT,
                    status TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO orders (item_id, quantity, customer, status) VALUES "
                "(1, 5, 'A', 'pending'), (2, 1, 'B', 'approved')"
            )
        )
        conn.commit()
        conn.close()
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["permissions"] = ["view_orders"]
    return client


def test_export_csv(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/orders/export.csv")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("text/csv")
    assert b"A" in resp.data


def test_export_xlsx(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/orders/export.xlsx")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith(
        "application/vnd.openxmlformats-officedocument"
    )


def test_sorting(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/orders/list?sort=quantity&dir=desc")
    data = resp.get_json()
    assert data[0]["quantity"] == 5


def test_invalid_sort_defaults_to_id(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/orders/list?sort=bogus&dir=desc")
    data = resp.get_json()
    assert data[0]["id"] == 2


def test_invalid_direction_defaults_to_asc(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/orders/list?sort=quantity&dir=sideways")
    data = resp.get_json()
    assert data[0]["quantity"] == 1


