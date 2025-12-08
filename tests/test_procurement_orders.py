"""Tests for procurement purchase order workflows."""

import pytest


def _auth_headers(user):
    # Replace with helper that builds Authorization headers or session cookies.
    return {}


@pytest.fixture
def procurement_user(make_user_with_role):
    return make_user_with_role("procurement")


def test_full_procurement_flow(client, db_session, procurement_user):
    headers = _auth_headers(procurement_user)

    # 1) Create PO with 2 lines
    resp = client.post(
        "/api/procurement/orders",
        json={
            "supplier_id": 1,
            "supplier_name": "Vendor A",
            "currency": "ETB",
            "pi_number": "PI-12345",
            "awb_number": "AWB-555",
            "hs_code": "9001.10",
            "bank_name": "Commercial Bank",
            "customs_valuation": "12345.67",
            "efda_reference": "EFDA-REF-9",
            "lines": [
                {"item_code": "ITEM-1", "ordered_quantity": 10, "unit_price": 100},
                {"item_code": "ITEM-2", "ordered_quantity": 5, "unit_price": 200},
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    po = resp.get_json()
    assert po["pi_number"] == "PI-12345"
    assert po["awb_number"] == "AWB-555"
    assert po["hs_code"] == "9001.10"
    assert po["bank_name"] == "Commercial Bank"
    assert po["customs_valuation"] == 12345.67
    assert po["efda_reference"] == "EFDA-REF-9"
    po_id = po["id"]
    line_ids = [line["id"] for line in po["lines"]]

    # 2) Submit and approve
    resp = client.post(f"/api/procurement/orders/{po_id}/submit", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "submitted"

    resp = client.post(f"/api/procurement/orders/{po_id}/approve", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "approved"

    # 3) Partial receipt on line 1
    resp = client.post(
        f"/api/procurement/orders/{po_id}/receive",
        json={"lines": [{"line_id": line_ids[0], "quantity": 5}]},
        headers=headers,
    )
    assert resp.status_code == 200
    po_after = resp.get_json()
    assert po_after["status"] == "partially_received"
    l1 = [l for l in po_after["lines"] if l["id"] == line_ids[0]][0]
    assert l1["received_quantity"] == 5

    # 4) Receive rest
    resp = client.post(
        f"/api/procurement/orders/{po_id}/receive",
        json={
            "lines": [
                {"line_id": line_ids[0], "quantity": 5},
                {"line_id": line_ids[1], "quantity": 5},
            ]
        },
        headers=headers,
    )
    assert resp.status_code == 200
    po_final = resp.get_json()
    assert po_final["status"] == "received"
    for line in po_final["lines"]:
        assert line["received_quantity"] == line["ordered_quantity"]


def test_ticket_serialization_includes_trade_fields(client, db_session, procurement_user):
    headers = _auth_headers(procurement_user)

    po_resp = client.post(
        "/api/procurement/orders",
        json={
            "supplier_id": 5,
            "pi_number": "PI-555",
            "awb_number": "AWB-123",
            "hs_code": "0101.10",
            "efda_reference": "EFDA-10",
            "bank_name": "Commercial Bank",
            "customs_valuation": "12000.55",
            "lines": [{"item_code": "ITEM-TR", "ordered_quantity": 1, "unit_price": 50}],
        },
        headers=headers,
    )
    assert po_resp.status_code == 201
    po_id = po_resp.get_json()["id"]

    ticket_resp = client.post(
        "/api/procurement/tickets",
        json={"title": "Import batch", "purchase_order_id": po_id},
        headers=headers,
    )
    assert ticket_resp.status_code == 201
    payload = ticket_resp.get_json()
    assert payload["purchase_order"]["pi_number"] == "PI-555"
    assert payload["purchase_order"]["awb_number"] == "AWB-123"
    assert payload["purchase_order"]["hs_code"] == "0101.10"
    assert payload["purchase_order"]["efda_reference"] == "EFDA-10"
    assert payload["purchase_order"]["bank_name"] == "Commercial Bank"
    assert payload["purchase_order"]["customs_valuation"] == 12000.55
    assert payload["purchase_order"]["currency"] == "ETB"


def test_cannot_receive_more_than_ordered(client, db_session, procurement_user):
    headers = _auth_headers(procurement_user)

    resp = client.post(
        "/api/procurement/orders",
        json={
            "supplier_id": 1,
            "lines": [{"item_code": "ITEM-OVER", "ordered_quantity": 5, "unit_price": 10}],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    po = resp.get_json()
    po_id = po["id"]
    line_id = po["lines"][0]["id"]

    client.post(f"/api/procurement/orders/{po_id}/submit", headers=headers)
    client.post(f"/api/procurement/orders/{po_id}/approve", headers=headers)

    # First receipt OK
    resp = client.post(
        f"/api/procurement/orders/{po_id}/receive",
        json={"lines": [{"line_id": line_id, "quantity": 5}]},
        headers=headers,
    )
    assert resp.status_code == 200

    # Second receipt should fail
    resp = client.post(
        f"/api/procurement/orders/{po_id}/receive",
        json={"lines": [{"line_id": line_id, "quantity": 1}]},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "cannot receive goods in status received" in resp.get_json()["error"]


def test_milestone_requires_geo_when_completed(client, db_session, procurement_user):
    headers = _auth_headers(procurement_user)

    # Create a ticket
    ticket_resp = client.post(
        "/api/procurement/tickets",
        json={"title": "Import lot A"},
        headers=headers,
    )
    assert ticket_resp.status_code == 201
    ticket_id = ticket_resp.get_json()["id"]

    # Attempt to complete milestone without geo should fail
    bad_resp = client.post(
        f"/api/procurement/tickets/{ticket_id}/milestones",
        json={"name": "Arrived customs", "status": "completed"},
        headers=headers,
    )
    assert bad_resp.status_code == 400
    assert "geo_lat" in bad_resp.get_json()["error"]

    # Valid geo payload passes and is returned
    good_resp = client.post(
        f"/api/procurement/tickets/{ticket_id}/milestones",
        json={
            "name": "Arrived customs",
            "status": "completed",
            "geo_lat": 9.0101,
            "geo_lng": 38.7607,
            "geo_accuracy_m": 12.3,
        },
        headers=headers,
    )
    assert good_resp.status_code == 201
    payload = good_resp.get_json()
    assert payload["milestones"][0]["geo"]["lat"] == 9.0101
    assert payload["milestones"][0]["geo"]["lng"] == 38.7607
