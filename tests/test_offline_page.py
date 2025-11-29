from erp import create_app


def test_offline_page_available():
    app = create_app()
    client = app.test_client()
    resp = client.get("/offline")
    assert resp.status_code == 200
    assert resp.mimetype == "text/html"
    assert resp.get_data(as_text=True) == "<html><body>The application is offline</body></html>"


