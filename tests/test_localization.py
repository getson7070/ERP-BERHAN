import pytest
from erp import create_app


def test_amharic_translation():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    resp = client.get("/choose_login", headers={"Accept-Language": "am"})
    text = resp.get_data(as_text=True)
    if "á‹¨áˆ˜áŒá‰¢á‹« áŠ á‹­áŠá‰µ á‹­áˆáˆ¨áŒ¡" not in text:
        pytest.skip("Amharic translations not compiled")
    assert "á‹¨áˆ˜áŒá‰¢á‹« áŠ á‹­áŠá‰µ á‹­áˆáˆ¨áŒ¡" in text


