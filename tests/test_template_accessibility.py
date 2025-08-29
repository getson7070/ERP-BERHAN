import pathlib
import pytest

pytest.importorskip("bs4")
from bs4 import BeautifulSoup

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
