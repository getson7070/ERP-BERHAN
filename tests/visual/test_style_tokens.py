from pathlib import Path

import bs4

TEMPLATE = Path("templates/base.html").read_text(encoding="utf-8")
NAVBAR = Path("templates/partials/navbar.html").read_text(encoding="utf-8")


def test_base_has_viewport_meta():
    soup = bs4.BeautifulSoup(TEMPLATE, "html.parser")
    viewport = soup.find("meta", attrs={"name": "viewport"})
    assert viewport is not None


def test_html_declares_theme():
    soup = bs4.BeautifulSoup(TEMPLATE, "html.parser")
    html = soup.find("html")
    assert html.get("data-bs-theme") == "light"


def test_navbar_has_theme_toggle():
    soup = bs4.BeautifulSoup(NAVBAR, "html.parser")
    toggle = soup.find(id="themeToggle")
    assert toggle is not None
