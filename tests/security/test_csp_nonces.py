from pathlib import Path

from bs4 import BeautifulSoup

TEMPLATE_DIR = Path("templates")


def test_inline_scripts_have_nonce():
    for html_file in TEMPLATE_DIR.rglob("*.html"):
        soup = BeautifulSoup(html_file.read_text(), "html.parser")
        for script in soup.find_all("script"):
            if script.get("src"):
                continue
            assert script.has_attr("nonce"), f"{html_file} inline script missing nonce"
