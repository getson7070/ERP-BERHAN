from datetime import datetime, timedelta
from http import HTTPStatus

from erp.extensions import db
from erp.models import GeoLastLocation, GeoPing


def test_ping_validates_coordinates(app, client):
    resp = client.post(
        "/api/geo/ping",
        json={"subject_type": "user", "subject_id": 1, "lat": 150, "lng": 10},
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "latitude" in resp.get_json()["error"]


def test_ping_persists_last_location(app, client):
    resp = client.post(
        "/api/geo/ping",
        json={"subject_type": "user", "subject_id": 1, "lat": 9.01, "lng": 38.75},
    )
    assert resp.status_code == HTTPStatus.CREATED
    payload = resp.get_json()
    assert payload["lat"] == 9.01
    assert payload["lng"] == 38.75

    with app.app_context():
        ping_count = GeoPing.query.count()
        assert ping_count == 1
        last = GeoLastLocation.query.first()
        assert last is not None
        assert float(last.lat) == 9.01
        assert float(last.lng) == 38.75


def test_offline_endpoint_detects_stale(app, client):
    with app.app_context():
        stale_time = datetime.utcnow() - timedelta(minutes=90)
        db.session.add(
            GeoLastLocation(
                id=999,
                org_id=1,
                subject_type="user",
                subject_id=42,
                lat=9.02,
                lng=38.76,
                updated_at=stale_time,
            )
        )
        db.session.commit()

    resp = client.get("/api/geo/offline?minutes=60")
    assert resp.status_code == HTTPStatus.OK
    data = resp.get_json()
    assert data["count"] == 1
    assert data["offline"][0]["subject_id"] == 42
    assert data["offline"][0]["status"] == "offline"
