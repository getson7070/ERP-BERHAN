import importlib, pytest

def create_client():
    erp = importlib.import_module("erp")
    create_app = getattr(erp, "create_app")
    app = create_app(testing=True) if "testing" in create_app.__code__.co_varnames else create_app()
    return app.test_client()

@pytest.mark.timeout(30)
def test_status_200():
    c = create_client()
    r = c.get("/status")
    assert r.status_code == 200
    assert r.is_json

def test_doctor_semantics():
    c = create_client()
    r = c.get("/ops/doctor")
    assert r.status_code in (200, 503)
    payload = r.get_json()
    assert isinstance(payload, dict) and "ok" in payload and "checks" in payload