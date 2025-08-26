import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app, oauth


def test_oauth_login_redirect(monkeypatch):
    app = create_app()
    app.config.update({
        'OAUTH_CLIENT_ID': 'id',
        'OAUTH_CLIENT_SECRET': 'sec',
        'OAUTH_AUTH_URL': 'https://sso.example/authorize',
        'OAUTH_TOKEN_URL': 'https://sso.example/token',
        'OAUTH_USERINFO_URL': 'https://sso.example/userinfo',
    })
    oauth.register(
        'sso',
        client_id='id',
        client_secret='sec',
        access_token_url='https://sso.example/token',
        authorize_url='https://sso.example/authorize',
        client_kwargs={'scope': 'openid'},
    )
    client = app.test_client()
    rv = client.get('/oauth_login')
    assert rv.status_code == 302
    assert 'sso.example/authorize' in rv.location
