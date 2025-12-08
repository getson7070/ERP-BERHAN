import json
from http import HTTPStatus


def _create_work_order(client, title="Geo required WO"):
    res = client.post(
        "/api/maintenance/work-orders",
        json={"title": title, "description": "geo coverage"},
        headers={"Accept": "application/json"},
    )
    assert res.status_code in (HTTPStatus.CREATED, HTTPStatus.OK), res.data
    payload = json.loads(res.data)
    return payload["id"]


def test_start_requires_geo_coordinates(client):
    work_order_id = _create_work_order(client)

    # Missing coordinates should be rejected.
    res = client.post(
        f"/api/maintenance/work-orders/{work_order_id}/start",
        json={},
        headers={"Accept": "application/json"},
    )
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert b"lat and lng are required" in res.data

    # Providing coordinates should allow start.
    res_ok = client.post(
        f"/api/maintenance/work-orders/{work_order_id}/start",
        json={"lat": 9.01001, "lng": 38.7612},
        headers={"Accept": "application/json"},
    )
    assert res_ok.status_code == HTTPStatus.OK
    payload = json.loads(res_ok.data)
    assert payload["start_lat"] == 9.01001
    assert payload["start_lng"] == 38.7612


def test_check_in_requires_geo_coordinates(client):
    work_order_id = _create_work_order(client, title="Geo check-in")
    # Start with coordinates so check-in can proceed.
    start_res = client.post(
        f"/api/maintenance/work-orders/{work_order_id}/start",
        json={"lat": 9.01, "lng": 38.76},
        headers={"Accept": "application/json"},
    )
    assert start_res.status_code == HTTPStatus.OK

    # Reject check-in without geo.
    res = client.post(
        f"/api/maintenance/work-orders/{work_order_id}/check-in",
        json={},
        headers={"Accept": "application/json"},
    )
    assert res.status_code == HTTPStatus.BAD_REQUEST
    assert b"lat and lng are required" in res.data

    res_ok = client.post(
        f"/api/maintenance/work-orders/{work_order_id}/check-in",
        json={"lat": 9.01234, "lng": 38.76543},
        headers={"Accept": "application/json"},
    )
    assert res_ok.status_code == HTTPStatus.OK
    payload = json.loads(res_ok.data)
    assert payload["start_lat"] == 9.01 or payload["start_lat"] == 9.01234
    assert payload["start_lng"] == 38.76 or payload["start_lng"] == 38.76543
