def test_factory_health():
    from erp import create_app
    app = create_app()
    client = app.test_client()
    assert client.get('/health').status_code == 200
    assert client.get('/health/ready').status_code == 200
