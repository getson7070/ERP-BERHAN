from sqlalchemy import text

from erp import create_app
from db import get_db


def test_cross_tenant_inventory_access(tmp_path, monkeypatch):
    db_file = tmp_path / "rls_access.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    app = create_app()
    app.config.update(TESTING=True)
    with app.app_context():
        conn = get_db()
        conn.execute(
            text(
                "INSERT INTO inventory_items (org_id, name, sku, quantity) VALUES"
                " (1,'A','A1',1), (2,'B','B2',1)"
            )
        )
        conn.commit()
        conn.close()
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["org_id"] = 1
    resp = client.post("/inventory/2", data={"name": "hack"})
    assert resp.status_code in (400, 403, 404)
    with app.app_context():
        conn = get_db()
        row = conn.execute(
            text("SELECT name FROM inventory_items WHERE id = 2")
        ).fetchone()
        assert row[0] == "B"
        conn.close()
    resp = client.get("/inventory/")
    assert b"B2" not in resp.data


