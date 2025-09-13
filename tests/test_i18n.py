import pytest

pytest.importorskip("bs4")
from erp import create_app  # noqa: E402


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_language_switch(client):
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["role"] = "Employee"
    client.get("/set_language/am", follow_redirects=True)
    res = client.get("/dashboard")
    html = res.get_data(as_text=True)
    assert 'lang="am"' in html


def test_locale_switcher_rendered(client):
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["role"] = "Employee"
    res = client.get("/dashboard")
    html = res.get_data(as_text=True)
    assert 'id="lang-select"' in html
    assert '<option value="am"' in html
