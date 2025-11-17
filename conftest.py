import importlib.util
import os

import pytest

from erp import create_app, db
from erp.models import Organization


def pytest_addoption(parser):
    """Register coverage flags when pytest-cov is missing to avoid arg errors."""

    if importlib.util.find_spec("pytest_cov") is not None:
        return

    parser.addoption("--cov", action="store", default=None)
    parser.addoption("--cov-report", action="store", default=None)
    parser.addoption("--cov-branch", action="store_true", default=False)
    parser.addoption("--cov-fail-under", action="store", default=None)


def _prepare_app():
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, LOGIN_DISABLED=True)
    with app.app_context():
        db.create_all()
        if not Organization.query.filter_by(id=1).first():
            db.session.add(Organization(id=1, name="Test Org"))
            db.session.commit()
    return app


@pytest.fixture(scope="session")
def app():
    app = _prepare_app()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    with app.test_client(use_cookies=True) as client:
        yield client
