from datetime import datetime, timedelta

import pytest


@pytest.fixture
def org_id(resolve_org_id):
    return resolve_org_id()


def test_ping_ignored_without_consent(client, db_session, org_id):
    from erp.models import GeoLastLocation, MarketingConsent

    db_session.add(
        MarketingConsent(
            org_id=org_id,
            subject_type="user",
            subject_id=1,
            marketing_opt_in=True,
            location_opt_in=False,
        )
    )
    db_session.commit()

    resp = client.post(
        "/api/geo/ping",
        json={"subject_type": "user", "subject_id": 1, "lat": 9.0, "lng": 38.7},
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ignored_no_consent"
    assert (
        GeoLastLocation.query.filter_by(org_id=org_id, subject_type="user", subject_id=1).first()
        is None
    )


def test_offline_alert_created(db_session, org_id):
    from erp.models import FinanceAuditLog, GeoAssignment, GeoLastLocation
    from erp.tasks.geo_offline import check_offline_subjects

    db_session.add(
        GeoAssignment(
            org_id=org_id,
            subject_type="user",
            subject_id=5,
            task_type="delivery",
            task_id=99,
            status="active",
        )
    )
    db_session.add(
        GeoLastLocation(
            org_id=org_id,
            subject_type="user",
            subject_id=5,
            lat=9.01,
            lng=38.75,
            updated_at=datetime.utcnow() - timedelta(hours=2),
        )
    )
    db_session.commit()

    check_offline_subjects(minutes=30)

    alert = FinanceAuditLog.query.filter_by(org_id=org_id, event_type="GEO_OFFLINE_ALERT").first()
    assert alert is not None
