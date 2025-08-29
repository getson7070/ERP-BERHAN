import pathlib

from bs4 import BeautifulSoup

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]


def test_base_template_has_dark_mode():
    base_html = (BASE_DIR / "templates" / "base.html").read_text()
    soup = BeautifulSoup(base_html, "html.parser")
    html_tag = soup.find("html")
    assert html_tag is not None
    assert html_tag.get("data-bs-theme") == "light"


def test_dashboard_css_has_focus_state():
    css = (BASE_DIR / "static" / "css" / "dashboard.css").read_text()
    assert ":focus-visible" in css
