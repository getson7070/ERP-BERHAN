import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app


def test_status_route():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    resp = client.get("/status")
    assert resp.status_code == 200
    assert b"System Status" in resp.data
    assert b"Error budget remaining" in resp.data
    assert b"Incident runbook highlights" in resp.data
