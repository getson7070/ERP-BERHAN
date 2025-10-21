import pytest
from erp import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client(use_cookies=True) as c:
        yield c
