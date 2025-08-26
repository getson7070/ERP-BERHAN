import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app


def test_help_route():
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()
    resp = client.get('/help')
    assert resp.status_code == 200
    assert b'Help Center' in resp.data
