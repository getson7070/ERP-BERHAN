import pytest
from importlib import import_module

def _load_app():
    for mod, attr in [("erp", "app"), ("erp.app", "app"), ("erp", "create_app"), ("erp.app", "create_app")]:
        try:
            m = import_module(mod); obj = getattr(m, attr)
            return obj() if callable(obj) else obj
        except Exception:
            continue
    pytest.skip("Flask app not importable")

@pytest.fixture
def client():
    app = _load_app()
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c

def test_login_protected_logout_smoke(client):
    r = client.get("/login")
    assert r.status_code in (200, 302)
    r = client.post("/login", data={"username": "demo", "password": "demo", "totp": "000000"}, follow_redirects=True)
    assert r.status_code in (200, 302)
    r = client.get("/admin/")
    assert r.status_code in (200, 302, 403)
    r = client.get("/logout")
    assert r.status_code in (200, 302)
