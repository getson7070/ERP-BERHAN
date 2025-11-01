from erp import create_app

def test_csrf_enabled():
    app = create_app()
    assert app.extensions.get('csrf') is not None, "CSRF extension not registered"
