import importlib.util
import os

import pytest
from sqlalchemy.orm import scoped_session, sessionmaker

LIGHTWEIGHT_TEST_MODE = os.getenv("LIGHTWEIGHT_TEST_MODE") == "1"

if not LIGHTWEIGHT_TEST_MODE:
    import importlib

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


if not LIGHTWEIGHT_TEST_MODE:


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


    @pytest.fixture()
    def db_session(app):
        """Provide a scoped session wrapped in a transaction per test."""

        with app.app_context():
            connection = db.engine.connect()
            transaction = connection.begin()
            Session = scoped_session(sessionmaker(bind=connection))
            db.session = Session
            try:
                yield Session
                Session.commit()
            finally:
                Session.remove()
                transaction.rollback()
                connection.close()


    @pytest.fixture()
    def org_id(app):
        """Default test organisation identifier."""

        return 1


    @pytest.fixture()
    def resolve_org_id(org_id):
        """Return a resolver callable matching app code expectations."""

        return lambda: org_id
else:

    @pytest.fixture(scope="session")
    def app():
        pytest.skip("LIGHTWEIGHT_TEST_MODE enabled; app fixture unavailable")


    @pytest.fixture()
    def client():
        pytest.skip("LIGHTWEIGHT_TEST_MODE enabled; client fixture unavailable")
