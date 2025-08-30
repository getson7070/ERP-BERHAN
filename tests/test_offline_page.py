from erp import create_app


def test_offline_page_available():
    app = create_app()
    client = app.test_client()
    resp = client.get("/offline")
    assert b"The application is offline" in resp.data
