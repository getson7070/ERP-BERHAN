import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app  # noqa: E402


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


def test_language_switch(client):
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['role'] = 'Employee'
    client.get('/set_language/am', follow_redirects=True)
    res = client.get('/dashboard')
    assert 'የሰራተኛ ዳሽቦርድ' in res.get_data(as_text=True)
