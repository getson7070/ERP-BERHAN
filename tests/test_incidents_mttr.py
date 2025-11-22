from datetime import datetime, timedelta

from erp import db
from erp.models import Incident


def test_mttr_endpoint_reports_average(client, app):
    with app.app_context():
        incident = Incident(
            org_id=1,
            service="banking",
            started_at=datetime.utcnow() - timedelta(minutes=45),
            recovered_at=datetime.utcnow(),
            status="recovered",
        )
        db.session.add(incident)
        db.session.commit()

    resp = client.get("/api/reliability/mttr")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 1
    assert data["mttr_minutes"] >= 44
