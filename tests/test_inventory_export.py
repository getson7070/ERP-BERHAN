import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))  # noqa: E402

from erp import create_app  # noqa: E402
from erp.models import db, Inventory  # noqa: E402


def _setup_app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "inv.db"))
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        db.session.add_all([
            Inventory(org_id=1, name="A", sku="a", quantity=1),
            Inventory(org_id=1, name="B", sku="b", quantity=5),
        ])
        db.session.commit()
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["org_id"] = 1
    return client


def test_export_csv(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/inventory/export")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("text/csv")
    assert b"a" in resp.data


def test_export_xlsx(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/inventory/export?format=xlsx")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith(
        "application/vnd.openxmlformats-officedocument"
    )


def test_sorting(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/inventory/?sort=quantity&order=desc")
    data = resp.get_json()
    assert data[0]["quantity"] == 5
