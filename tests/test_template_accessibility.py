import pathlib
import pytest

pytest.importorskip("bs4")
from bs4 import BeautifulSoup  # noqa: E402

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]


def test_base_template_has_dark_mode():
    base_html = (BASE_DIR / "templates" / "base.html").read_text()
    soup = BeautifulSoup(base_html, "html.parser")
    html_tag = soup.find("html")
    assert html_tag is not None  # nosec B101
    assert html_tag.get("data-bs-theme") == "light"  # nosec B101


def test_dashboard_css_has_focus_state():
    css = (BASE_DIR / "static" / "css" / "dashboard.css").read_text()
    assert ":focus-visible" in css  # nosec B101


@pytest.mark.accessibility
def test_base_template_axe():
    pytest.importorskip("playwright.sync_api")
    pytest.importorskip("axe_playwright_python")
    from playwright.sync_api import sync_playwright
    from axe_playwright_python.sync_playwright import Axe
    import json

    with sync_playwright() as p:
        browser = p.firefox.launch()
        page = browser.new_page()
        page.goto((BASE_DIR / "templates" / "base.html").as_uri())
        axe = Axe()
        options = json.dumps({"rules": {"html-lang-valid": {"enabled": False}}})
        results = axe.run(page, options=options)
        assert results.violations_count == 0  # nosec B101
        browser.close()


def test_show_message_sanitizes_html():
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.firefox.launch()
        page = browser.new_page()
        page.goto((BASE_DIR / "templates" / "base.html").as_uri())
        page.evaluate("showMessage('info', '<img src=x onerror=alert(1)>')")
        content = page.inner_html("#messages .alert")
        assert "<img" not in content  # nosec B101
        assert "&lt;img src=x onerror=alert(1)&gt;" in content  # nosec B101
        browser.close()


def test_fetch_omits_csrf_on_cross_origin():
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    captured = {}

    with sync_playwright() as p:
        browser = p.firefox.launch()
        page = browser.new_page()
        page.goto((BASE_DIR / "templates" / "base.html").as_uri())

        def handle(route, request):
            captured["headers"] = request.headers
            route.fulfill(status=200, body="ok")

        page.route("https://example.com/*", handle)
        page.evaluate("fetch('https://example.com/test')")
        assert "x-csrftoken" not in captured.get("headers", {})  # nosec B101
        browser.close()
