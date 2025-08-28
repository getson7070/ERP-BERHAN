from pathlib import Path

import bs4

TEMPLATE = Path("templates/base.html").read_text(encoding="utf-8")


def test_base_has_viewport_meta():
    soup = bs4.BeautifulSoup(TEMPLATE, "html.parser")
    viewport = soup.find("meta", attrs={"name": "viewport"})
    assert viewport is not None
