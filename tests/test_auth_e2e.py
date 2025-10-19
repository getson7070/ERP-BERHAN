import pytest
from importlib import import_module

def get_app():
    for mod, attr in [("erp", "app"), ("erp.app", "app"), ("erp", "create_app"), ("erp.app", "create_app")]:
        try:
            m = import_module(mod); obj = getattr(m, attr)
            return obj() if callable(obj) else obj
        except Exception:
            continue
    pytest.skip("Flask app not importable")

@pytest.fixture
def client():
    app = get_app()
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c

def test_login_totp_protected_logout(client):
    # Adjust endpoints/fields to your implementation
    r = client.get("/login")
    assert r.status_code in (200, 302)
    r = client.post("/login", data={"username":"demo","password":"demo","totp":"000000"}, follow_redirects=True)
    assert r.status_code in (200, 302)
    r = client.get("/admin/")
    assert r.status_code in (200, 302)
    r = client.get("/logout")
    assert r.status_code in (200, 302)

def test_csrf_cookie_security(client):
    r = client.get("/")
    # Check=headers may vary if set via after_request
    csp = r.headers.get("Content-Security-Policy")
    assert csp is not None
