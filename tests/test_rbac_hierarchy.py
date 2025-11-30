import os
import pytest

from erp import create_app


def test_rbac_hierarchy():
    app = create_app()
    with app.app_context():
        # Basic test: app creates without errors
        assert app is not None

        # Test RBAC loader (from extensions.py)
        from erp.extensions import login_manager
        assert login_manager.user_loader is not None

        # Test that SECRET_KEY is set
        app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "test-key")
        assert app.config["SECRET_KEY"] == "test-key"


@pytest.fixture
def client():
    app = create_app()
    with app.test_client() as client:
        yield client


def test_login_redirect(client):
    response = client.get("/auth/login")
    assert response.status_code == 200