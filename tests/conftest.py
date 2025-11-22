import os

import pytest

LIGHTWEIGHT_TEST_MODE = os.getenv("LIGHTWEIGHT_TEST_MODE") == "1"

if not LIGHTWEIGHT_TEST_MODE:
    from erp import create_app, db
    from erp.models import Organization


@pytest.fixture
def app():
    if LIGHTWEIGHT_TEST_MODE:
        pytest.skip("LIGHTWEIGHT_TEST_MODE enabled; app fixture unavailable")

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, LOGIN_DISABLED=True)
    with app.app_context():
        db.create_all()
        if not Organization.query.filter_by(id=1).first():
            db.session.add(Organization(id=1, name="Test Org"))
            db.session.commit()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
