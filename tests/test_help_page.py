import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app


def test_help_route():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    resp = client.get("/help")
    assert resp.status_code == 200
    assert b"Help Center" in resp.data
    assert b"support@example.com" in resp.data


def test_help_support_overrides(monkeypatch):
    monkeypatch.setenv("SUPPORT_EMAIL", "help@erp.test")
    monkeypatch.setenv("SUPPORT_PHONE", "+251-123-456")
    monkeypatch.setenv("SUPPORT_HOURS", "24/7")
    monkeypatch.setenv("SUPPORT_RESPONSE_SLA", "2 hours")

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    resp = client.get("/help")

    assert resp.status_code == 200
    assert b"help@erp.test" in resp.data
    assert b"+251-123-456" in resp.data
    assert b"24/7" in resp.data
    assert b"2 hours" in resp.data


