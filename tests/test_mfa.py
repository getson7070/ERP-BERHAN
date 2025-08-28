import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app


def test_admin_panel_requires_mfa(tmp_path, monkeypatch):
    monkeypatch.setenv("MFA_ENABLED", "true")
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["user_id"] = 1  # simulate logged-in user without MFA
        resp = client.get("/admin/panel")
        assert resp.status_code == 403
        with client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["user_id"] = 1
            sess["mfa_verified"] = True
        resp = client.get("/admin/panel")
        assert resp.status_code == 200
        assert b"admin panel" in resp.data
