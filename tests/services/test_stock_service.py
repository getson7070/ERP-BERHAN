from __future__ import annotations

import uuid

import pytest

from erp.extensions import db
from erp.inventory.models import Item, StockBalance, StockLedgerEntry, Warehouse
from erp.services.stock_service import StockService


@pytest.fixture
def org_id() -> int:
    return 1


@pytest.fixture
def base_inventory_objects(db_session, org_id):
    item = Item(
        id=uuid.uuid4(),
        sku="TEST-SKU-001",
        name="Test Item",
    )
    warehouse = Warehouse(
        id=uuid.uuid4(),
        name="Main Warehouse",
        org_id=org_id,
        is_default=True,
    )
    db.session.add_all([item, warehouse])
    db.session.flush()
    return {"item": item, "warehouse": warehouse}


def _get_balance(org_id: int, item_id, warehouse_id):
    return (
        StockBalance.query.filter_by(
            org_id=org_id,
            item_id=item_id,
            warehouse_id=warehouse_id,
        )
        .with_for_update(read=False)
        .one_or_none()
    )


def _get_ledger(org_id: int, item_id, warehouse_id):
    return StockLedgerEntry.query.filter_by(
        org_id=org_id, item_id=item_id, warehouse_id=warehouse_id
    ).all()


def test_increment_creates_new_balance(db_session, org_id, base_inventory_objects):
    item = base_inventory_objects["item"]
    warehouse = base_inventory_objects["warehouse"]

    svc = StockService()

    svc.increment(
        org_id=org_id,
        item_id=item.id,
        warehouse_id=warehouse.id,
        qty=10,
        reason="test_increment",
        ref_type="unit_test",
        ref_id=1,
    )

    bal = _get_balance(org_id, item.id, warehouse.id)
    assert bal is not None
    assert float(bal.qty_on_hand) == pytest.approx(10.0)

    ledgers = _get_ledger(org_id, item.id, warehouse.id)
    assert len(ledgers) == 1
    assert float(ledgers[0].qty) == pytest.approx(10.0)


def test_increment_adds_to_existing_balance(db_session, org_id, base_inventory_objects):
    item = base_inventory_objects["item"]
    warehouse = base_inventory_objects["warehouse"]

    svc = StockService()

    svc.increment(
        org_id=org_id,
        item_id=item.id,
        warehouse_id=warehouse.id,
        qty=5,
        reason="first",
        ref_type="unit_test",
        ref_id=1,
    )
    svc.increment(
        org_id=org_id,
        item_id=item.id,
        warehouse_id=warehouse.id,
        qty=7.5,
        reason="second",
        ref_type="unit_test",
        ref_id=2,
    )

    bal = _get_balance(org_id, item.id, warehouse.id)
    assert bal is not None
    assert float(bal.qty_on_hand) == pytest.approx(12.5)

    ledgers = _get_ledger(org_id, item.id, warehouse.id)
    assert len(ledgers) == 2
    assert float(ledgers[-1].qty) == pytest.approx(7.5)


def test_decrement_blocks_negative_stock(db_session, org_id, base_inventory_objects):
    item = base_inventory_objects["item"]
    warehouse = base_inventory_objects["warehouse"]

    svc = StockService()

    svc.increment(
        org_id=org_id,
        item_id=item.id,
        warehouse_id=warehouse.id,
        qty=3,
        reason="seed",
        ref_type="unit_test",
        ref_id=1,
    )

    svc.decrement(
        org_id=org_id,
        item_id=item.id,
        warehouse_id=warehouse.id,
        qty=2,
        reason="consume",
        ref_type="unit_test",
        ref_id=2,
    )

    bal = _get_balance(org_id, item.id, warehouse.id)
    assert float(bal.qty_on_hand) == pytest.approx(1.0)

    with pytest.raises(ValueError):
        svc.decrement(
            org_id=org_id,
            item_id=item.id,
            warehouse_id=warehouse.id,
            qty=2,
            reason="over-consume",
            ref_type="unit_test",
            ref_id=3,
        )

    db.session.rollback()

    bal_after = _get_balance(org_id, item.id, warehouse.id)
    assert float(bal_after.qty_on_hand) == pytest.approx(1.0)



def test_set_quantity_creates_and_updates(db_session, org_id, base_inventory_objects):
    item = base_inventory_objects["item"]
    warehouse = base_inventory_objects["warehouse"]

    svc = StockService()

    svc.set_quantity(
        org_id=org_id,
        item_id=item.id,
        warehouse_id=warehouse.id,
        new_qty=10,
        reason="initial_count",
        ref_type="stock_count",
        ref_id=1,
    )

    bal = _get_balance(org_id, item.id, warehouse.id)
    assert bal is not None
    assert float(bal.qty_on_hand) == pytest.approx(10.0)

    svc.set_quantity(
        org_id=org_id,
        item_id=item.id,
        warehouse_id=warehouse.id,
        new_qty=4,
        reason="adjustment",
        ref_type="stock_count",
        ref_id=2,
    )

    bal2 = _get_balance(org_id, item.id, warehouse.id)
    assert float(bal2.qty_on_hand) == pytest.approx(4.0)

    ledgers = _get_ledger(org_id, item.id, warehouse.id)
    assert len(ledgers) == 2


def test_get_available_quantity_handles_missing_row(db_session, org_id, base_inventory_objects):
    item = base_inventory_objects["item"]
    warehouse = base_inventory_objects["warehouse"]

    svc = StockService()

    assert svc.get_available_quantity(
        org_id=org_id,
        item_id=item.id,
        warehouse_id=warehouse.id,
    ) == pytest.approx(0.0)

    svc.increment(
        org_id=org_id,
        item_id=item.id,
        warehouse_id=warehouse.id,
        qty=2.5,
        reason="incoming",
        ref_type="unit_test",
        ref_id=1,
    )

    assert svc.get_available_quantity(
        org_id=org_id,
        item_id=item.id,
        warehouse_id=warehouse.id,
    ) == pytest.approx(2.5)
