from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from erp.inventory.models import StockBalance, StockLedgerEntry
from erp.models import Organization
from erp.services import stock_service


def _make_item_and_warehouse_ids():
    """Helper to keep IDs consistent and UUID-based."""
    return uuid.uuid4(), uuid.uuid4()


def test_stock_in_movement_updates_balance_and_ledger(db_session, resolve_org_id):
    """
    IN movement must:
    - create or update StockBalance for that (org, item, warehouse)
    - insert a StockLedgerEntry with matching qty
    - keep qty_on_hand in sync with cumulative ledger deltas
    """

    org_id = resolve_org_id()
    item_id, warehouse_id = _make_item_and_warehouse_ids()

    bal = StockBalance(
        org_id=org_id,
        item_id=item_id,
        warehouse_id=warehouse_id,
        qty_on_hand=Decimal("0"),
    )
    db_session.add(bal)
    db_session.commit()

    delta = Decimal("10")

    stock_service.create_stock_movement(
        org_id=org_id,
        item_id=item_id,
        warehouse_id=warehouse_id,
        delta_qty=delta,
        tx_type="inventory_adjustment",
        reference_type="test",
        reference_id="test-1",
    )

    db_session.flush()

    updated = (
        StockBalance.query.filter_by(org_id=org_id, item_id=item_id, warehouse_id=warehouse_id)
        .with_for_update()
        .first()
    )
    assert updated is not None
    assert Decimal(updated.qty_on_hand) == delta

    entries = (
        StockLedgerEntry.query.filter_by(org_id=org_id, item_id=item_id, warehouse_id=warehouse_id)
        .order_by(StockLedgerEntry.posting_time.asc())
        .all()
    )
    assert len(entries) == 1
    assert Decimal(entries[0].qty) == delta

    total_delta = sum(Decimal(e.qty) for e in entries)
    assert total_delta == Decimal(updated.qty_on_hand)


def test_stock_out_prevents_negative_by_default(db_session, resolve_org_id):
    """
    OUT movement that would drive stock below zero must fail by default.
    If you want to allow it, a caller must explicitly pass allow_negative=True.
    """

    org_id = resolve_org_id()
    item_id, warehouse_id = _make_item_and_warehouse_ids()

    bal = StockBalance(
        org_id=org_id,
        item_id=item_id,
        warehouse_id=warehouse_id,
        qty_on_hand=Decimal("5"),
    )
    db_session.add(bal)
    db_session.commit()

    db_session.add(
        StockLedgerEntry(
            org_id=org_id,
            item_id=item_id,
            warehouse_id=warehouse_id,
            qty=Decimal("5"),
            tx_type="seed",
        )
    )
    db_session.commit()

    with pytest.raises(ValueError):
        stock_service.create_stock_movement(
            org_id=org_id,
            item_id=item_id,
            warehouse_id=warehouse_id,
            delta_qty=Decimal("-10"),
            tx_type="inventory_adjustment",
            reference_type="test",
            reference_id="test-2",
        )

    fresh = StockBalance.query.filter_by(org_id=org_id, item_id=item_id, warehouse_id=warehouse_id).first()
    assert fresh is not None
    assert Decimal(fresh.qty_on_hand) == Decimal("5")

    entries = StockLedgerEntry.query.filter_by(org_id=org_id, item_id=item_id, warehouse_id=warehouse_id).all()
    assert len(entries) == 1


def test_stock_out_can_be_forced_with_allow_negative(db_session, resolve_org_id):
    """
    When explicitly requested, you can allow negative stock for emergency flows,
    but that must be intentional (allow_negative=True) and still keep ledger consistent.
    """

    org_id = resolve_org_id()
    item_id, warehouse_id = _make_item_and_warehouse_ids()

    bal = StockBalance(
        org_id=org_id,
        item_id=item_id,
        warehouse_id=warehouse_id,
        qty_on_hand=Decimal("5"),
    )
    db_session.add(bal)
    db_session.commit()

    db_session.add(
        StockLedgerEntry(
            org_id=org_id,
            item_id=item_id,
            warehouse_id=warehouse_id,
            qty=Decimal("5"),
            tx_type="seed",
        )
    )
    db_session.commit()

    stock_service.create_stock_movement(
        org_id=org_id,
        item_id=item_id,
        warehouse_id=warehouse_id,
        delta_qty=Decimal("-10"),
        tx_type="forced_adjustment",
        reference_type="test",
        reference_id="test-3",
        allow_negative=True,
    )

    db_session.flush()

    fresh = StockBalance.query.filter_by(org_id=org_id, item_id=item_id, warehouse_id=warehouse_id).first()
    assert Decimal(fresh.qty_on_hand) == Decimal("-5")

    entries = (
        StockLedgerEntry.query.filter_by(org_id=org_id, item_id=item_id, warehouse_id=warehouse_id)
        .order_by(StockLedgerEntry.posting_time.asc())
        .all()
    )
    assert len(entries) == 2
    assert Decimal(entries[-1].qty) == Decimal("-10")

    total_delta = sum(Decimal(e.qty) for e in entries)
    assert total_delta == Decimal(fresh.qty_on_hand)


def test_inventory_queries_must_be_org_scoped(db_session):
    """
    Smoke-test that your ORM-level inventory queries are always org-scoped.

    This is a guardrail above Postgres RLS:
    - Any developer who forgets `org_id` filtering will break this test.
    - It makes multi-tenant leaks much less likely at the application layer.
    """

    org_a = Organization(name="Org A")
    org_b = Organization(name="Org B")
    db_session.add_all([org_a, org_b])
    db_session.commit()

    item_a, warehouse_a = _make_item_and_warehouse_ids()
    item_b, warehouse_b = _make_item_and_warehouse_ids()

    db_session.add_all(
        [
            StockBalance(
                org_id=org_a.id,
                item_id=item_a,
                warehouse_id=warehouse_a,
                qty_on_hand=Decimal("100"),
            ),
            StockBalance(
                org_id=org_b.id,
                item_id=item_b,
                warehouse_id=warehouse_b,
                qty_on_hand=Decimal("200"),
            ),
        ]
    )
    db_session.commit()

    balances_for_a = StockBalance.query.filter_by(org_id=org_a.id).all()
    assert all(b.org_id == org_a.id for b in balances_for_a)
    assert {b.item_id for b in balances_for_a} == {item_a}

    balances_for_b = StockBalance.query.filter_by(org_id=org_b.id).all()
    assert all(b.org_id == org_b.id for b in balances_for_b)
    assert {b.item_id for b in balances_for_b} == {item_b}
