from decimal import Decimal
import uuid


def test_cycle_count_approval_adjusts_stock(client, db_session, resolve_org_id, make_user_with_role):
    org_id = resolve_org_id()

    # Baseline: set a stock balance manually
    from erp.inventory.models import StockBalance

    item_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()

    bal = StockBalance(org_id=org_id, item_id=item_id, warehouse_id=warehouse_id, qty_on_hand=Decimal("10"))
    db_session.add(bal)
    db_session.commit()

    inv_user = make_user_with_role("inventory")
    headers = {}

    resp = client.post(
        "/api/inventory/cycle-counts",
        json={
            "warehouse_id": str(warehouse_id),
            "lines": [
                {
                    "item_id": str(item_id),
                    "counted_qty": 8,
                }
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    cc_id = resp.get_json()["id"]

    client.post(f"/api/inventory/cycle-counts/{cc_id}/submit", headers=headers)
    client.post(f"/api/inventory/cycle-counts/{cc_id}/approve", headers=headers)

    bal2 = StockBalance.query.filter_by(org_id=org_id, item_id=item_id, warehouse_id=warehouse_id).first()
    assert bal2 is not None
    assert Decimal(bal2.qty_on_hand) == Decimal("8")
