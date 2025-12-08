import pytest

from erp import create_app
from erp.extensions import db


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("ALLOW_INSECURE_DEFAULTS", "1")
    monkeypatch.setenv("SECRET_KEY", "test-key")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")

    flask_app = create_app()
    flask_app.config.update(LOGIN_DISABLED=True, TESTING=True)

    with flask_app.app_context():
        db.create_all()

    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_admin_operational_analytics_template(client):
    resp = client.get("/admin/analytics/operations")
    assert resp.status_code == 200
    assert b"Operational Analytics" in resp.data


def test_admin_executive_analytics_template(client):
    resp = client.get("/admin/analytics/executive")
    assert resp.status_code == 200
    assert b"Executive Dashboard" in resp.data


def test_admin_bot_dashboard_template(client):
    resp = client.get("/admin/bots")
    assert resp.status_code == 200
    assert b"Telegram Bot Activity" in resp.data


def test_admin_rbac_template(client):
    resp = client.get("/admin/rbac")
    assert resp.status_code == 200
    assert b"RBAC Policies" in resp.data


def test_client_registration_template(client):
    resp = client.get("/auth/client/register")
    assert resp.status_code == 200
    assert b"Client onboarding" in resp.data or b"client onboarding" in resp.data


def test_maintenance_work_orders_template(client):
    resp = client.get("/maintenance/work-orders")
    assert resp.status_code == 200
    assert b"Work Orders" in resp.data or b"Work orders" in resp.data


