from datetime import date, timedelta

from erp import create_app
from erp.compliance.privacy import PrivacyImpactAssessment
from erp.models import Organization, User, db


def _login(client, user_id: int) -> None:
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["org_id"] = 1
        session["logged_in"] = True


def test_privacy_dashboard_lists_assessments():
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")

    with app.app_context():
        db.create_all()
        org = Organization(name="Test Org")
        db.session.add(org)
        db.session.commit()

        user_kwargs = {
            "email": "privacy@example.com",
            "password": "x",
            "fs_uniquifier": "privacy-1",
        }
        if hasattr(User, "org_id"):
            user_kwargs["org_id"] = org.id
        user = User(**user_kwargs)
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        assessment = PrivacyImpactAssessment(
            org_id=org.id,
            feature_key="analytics-export",
            feature_name="Analytics Export",
            status="dsr-open",
            risk_rating="high",
            assessment_date=date.today(),
            reviewer="Privacy Officer",
            dpia_reference="docs/dpia/analytics-export.md",
            next_review_due=date.today() + timedelta(days=20),
            mitigation_summary="Vendor DPA pending",
        )
        db.session.add(assessment)
        db.session.commit()

    client = app.test_client()
    _login(client, user_id)
    response = client.get("/privacy")
    assert response.status_code == 200
    body = response.data.decode()
    assert "Privacy & Compliance Center" in body
    assert "Analytics Export" in body
    assert "High-Risk Cases" in body
    assert "privacy@berhan.example" in body
