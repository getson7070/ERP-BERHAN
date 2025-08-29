from flask import json
import pytest

from erp import create_app
from erp.extensions import db
from erp.blueprints.inventory import (
    create_item,
    list_items,
    get_item,
    update_item,
    delete_item,
)
from sqlalchemy.exc import IntegrityError


def _unwrap(func):
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    return func


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    if db_path.exists():
        db_path.unlink()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    app = create_app()
    ctx = app.app_context()
    ctx.push()
    db.create_all()
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

    with app.test_request_context(
        json={"name": "Aspirin", "sku": "ASP-1", "quantity": 10}
    ):
        resp, status = create()
        assert status == 201
        item_id = json.loads(resp.data)["id"]
    with app.test_request_context(query_string={"sku": "ASP-1"}):
        resp = listing()
        data = json.loads(resp.data)
        assert data[0]["sku"] == "ASP-1"
    with app.test_request_context(json={"quantity": 15}):
        resp = update(item_id)
        assert json.loads(resp.data)["quantity"] == 15
    with app.test_request_context():
        resp = get(item_id)
        assert json.loads(resp.data)["sku"] == "ASP-1"
    with app.test_request_context():
        resp, status = delete(item_id)
        assert status == 204


def test_sku_uniqueness(app, monkeypatch):
    monkeypatch.setattr("erp.blueprints.inventory.get_jwt", lambda: {"org_id": 1})
    create = _unwrap(create_item)
    with app.test_request_context(json={"name": "Item1", "sku": "SKU1"}):
        create()
    with app.test_request_context(json={"name": "Item2", "sku": "SKU1"}):
        with pytest.raises(IntegrityError):
            create()


def test_pagination(app, monkeypatch):
    monkeypatch.setattr("erp.blueprints.inventory.get_jwt", lambda: {"org_id": 1})
    create = _unwrap(create_item)
    listing = _unwrap(list_items)
    for n in range(3):
        with app.test_request_context(json={"name": f"Item{n}", "sku": f"SKU{n}"}):
            create()
    with app.test_request_context(query_string={"limit": 2, "offset": 0}):
        resp = listing()
        assert len(json.loads(resp.data)) == 2
    with app.test_request_context(query_string={"limit": 2, "offset": 2}):
        resp = listing()
        assert len(json.loads(resp.data)) == 1
