from pathlib import Path
from typing import Tuple

from erp import create_app
from erp.db import db, User, Inventory


def setup_app(tmp_path: Path, monkeypatch) -> Tuple[object, int, int]:
    db_file = tmp_path / "inline.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with app.app_context():
        db.create_all()
        user = User(email="i@example.com", password="x", fs_uniquifier="u2")
        item = Inventory(name="Widget", sku="W1", quantity=5, org_id=1)
        db.session.add_all([user, item])
        db.session.commit()
        return app, user.id, item.id


def login(client, user_id):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["org_id"] = 1
        sess["logged_in"] = True


def test_inline_edit_updates_item(tmp_path, monkeypatch):
    app, user_id, item_id = setup_app(tmp_path, monkeypatch)
    client = app.test_client()
    login(client, user_id)
    resp = client.get("/inventory/")
    assert resp.status_code == 200
    resp = client.post(
        f"/inventory/{item_id}",
        data={"name": "Gadget", "sku": "W1", "quantity": "7"},
    )
    assert resp.json["sku"] == "W1"
    with app.app_context():
        item = Inventory.tenant_query(org_id=1).filter_by(id=item_id).first()
        assert item is not None
        assert item.name == "Gadget"



