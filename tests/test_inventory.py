from flask import json
import pytest

from erp import create_app
from erp.extensions import db
from erp.blueprints.inventory import create_item, list_items, get_item, update_item, delete_item


def _unwrap(func):
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    return func


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'test.db'}")
    app = create_app()
    ctx = app.app_context()
    ctx.push()
    yield app
    db.session.remove()
    db.drop_all()
    ctx.pop()


def test_inventory_crud(app, monkeypatch):
    monkeypatch.setattr("erp.blueprints.inventory.get_jwt", lambda: {"org_id": 1})
    create = _unwrap(create_item)
    listing = _unwrap(list_items)
    get = _unwrap(get_item)
    update = _unwrap(update_item)
    delete = _unwrap(delete_item)

    with app.test_request_context(json={"name": "Aspirin", "quantity": 10}):
        resp, status = create()
        assert status == 201
        item_id = json.loads(resp.data)["id"]
    with app.test_request_context():
        resp = listing()
        data = json.loads(resp.data)
        assert data[0]["name"] == "Aspirin"
    with app.test_request_context(json={"quantity": 15}):
        resp = update(item_id)
        assert json.loads(resp.data)["quantity"] == 15
    with app.test_request_context():
        resp = get(item_id)
        assert json.loads(resp.data)["name"] == "Aspirin"
    with app.test_request_context():
        resp, status = delete(item_id)
        assert status == 204
