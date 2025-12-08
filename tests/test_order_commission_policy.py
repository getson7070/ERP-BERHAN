from http import HTTPStatus
from decimal import Decimal
from datetime import datetime, UTC

import pytest

from erp.extensions import db
from erp.models import Inventory, Order, User


@pytest.fixture()
def sales_rep_id(app):
    with app.app_context():
        existing = User.query.filter_by(email="rep1@example.com").first()
        if existing:
            return existing.id
        rep = User(username="rep1", email="rep1@example.com", org_id=1)
        rep.password = "pass123!"
        db.session.add(rep)
        db.session.commit()
        return rep.id


@pytest.fixture()
def inventory_item(app):
    with app.app_context():
        existing = Inventory.query.filter_by(org_id=1, sku="SKU-1").first()
        if existing:
            return existing.id
        item = Inventory(org_id=1, name="Device", sku="SKU-1", quantity=5, price=Decimal("10"))
        db.session.add(item)
        db.session.commit()
        return item.id


def test_employee_initiated_defaults_commission_enabled(app, sales_rep_id):
    with app.app_context():
        order = Order(
            organization_id=1,
            total_amount=Decimal("100"),
            initiator_type="employee",
            assigned_sales_rep_id=sales_rep_id,
            commission_enabled=False,  # will be toggled explicitly
        )
        order.set_commission_enabled(True)
        assert order.commission_status == "pending"
        assert order.commission_block_reason == "awaiting payment settlement"

        order.set_payment_status("settled")
        assert order.commission_status == "eligible"
        assert order.commission_block_reason is None


def test_order_creation_requires_geo(app, inventory_item, client):
    resp = client.post(
        "/orders/",
        json={
            "items": [
                {"inventory_item_id": inventory_item, "quantity": 1, "unit_price": "10"},
            ],
            "initiator_type": "employee",
            "assigned_sales_rep_id": None,
            "commission_enabled": False,
        },
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "geo_lat" in resp.get_json()["error"]


def test_order_creation_validates_geo_ranges(app, inventory_item, client):
    resp = client.post(
        "/orders/",
        json={
            "items": [
                {"inventory_item_id": inventory_item, "quantity": 1, "unit_price": "10"},
            ],
            "initiator_type": "employee",
            "assigned_sales_rep_id": None,
            "commission_enabled": False,
            "geo_lat": 120,
            "geo_lng": 10,
        },
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "between -90 and 90" in resp.get_json()["error"]


def test_client_initiated_requires_management_approval(app, sales_rep_id, inventory_item, client):
    resp = client.post(
        "/orders/",
        json={
            "items": [
                {"inventory_item_id": inventory_item, "quantity": 1, "unit_price": "10"},
            ],
            "initiator_type": "client",
            "assigned_sales_rep_id": sales_rep_id,
            "commission_enabled": True,
            "geo_lat": 9.015,
            "geo_lng": 38.746,
        },
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN
    data = resp.get_json()
    assert "client-initiated commissions require management approval" in data["error"]


def test_management_override_allows_client_commission(app, sales_rep_id, inventory_item, client):
    resp = client.post(
        "/orders/",
        json={
            "items": [
                {"inventory_item_id": inventory_item, "quantity": 1, "unit_price": "10"},
            ],
            "initiator_type": "client",
            "assigned_sales_rep_id": sales_rep_id,
            "commission_enabled": True,
            "commission_approved_by_management": True,
            "geo_lat": 9.015,
            "geo_lng": 38.746,
        },
    )
    assert resp.status_code == HTTPStatus.CREATED
    payload = resp.get_json()
    assert payload["commission_status"] == "pending"
    assert payload["commission_block_reason"] == "awaiting payment settlement"

    # settle payment and ensure eligibility
    order_id = payload["id"]
    settle_resp = client.patch(
        f"/orders/{order_id}", json={"payment_status": "settled"}
    )
    assert settle_resp.status_code == HTTPStatus.OK
    updated = settle_resp.get_json()
    assert updated["commission_status"] == "eligible"
    assert updated["commission_block_reason"] is None
