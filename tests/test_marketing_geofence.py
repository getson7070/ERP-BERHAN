import pytest


def _auth_headers(user):
    return {}


@pytest.fixture
def marketing_user(make_user_with_role):
    return make_user_with_role("marketing")


def test_geofence_trigger_respects_consent(client, db_session, resolve_org_id):
    from erp.models import MarketingCampaign, MarketingGeofence, MarketingConsent

    org_id = resolve_org_id()

    campaign = MarketingCampaign(org_id=org_id, name="Test Campaign", status="active")
    db_session.add(campaign)
    db_session.flush()

    geofence = MarketingGeofence(
        org_id=org_id,
        campaign_id=campaign.id,
        name="HQ",
        center_lat=9.02,
        center_lng=38.75,
        radius_meters=500,
        action_type="notify",
    )
    db_session.add(geofence)

    consent = MarketingConsent(
        org_id=org_id,
        subject_type="client",
        subject_id=1,
        marketing_opt_in=True,
        location_opt_in=False,
    )
    db_session.add(consent)
    db_session.commit()

    resp = client.post(
        "/api/marketing/geofence/trigger",
        json={"subject_type": "client", "subject_id": 1, "lat": 9.0201, "lng": 38.7501},
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ignored_no_location_consent"
