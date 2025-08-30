from erp import create_app


def test_amharic_translation():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    resp = client.get("/choose_login", headers={"Accept-Language": "am"})
    assert "የመግቢያ አይነት ይምረጡ" in resp.get_data(as_text=True)
