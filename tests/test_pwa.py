import json
import pathlib
import pytest

pytest.importorskip("bs4")
from bs4 import BeautifulSoup  # noqa: E402

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]


def test_base_template_links_manifest():
    html = (BASE_DIR / "templates" / "base.html").read_text()
    soup = BeautifulSoup(html, "html.parser")
    manifest = soup.find("link", rel="manifest")
    assert manifest is not None  # nosec B101


def test_manifest_defines_icons():
    manifest_path = BASE_DIR / "static" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    sizes = {icon.get("sizes") for icon in manifest.get("icons", [])}
    assert {"192x192", "512x512"}.issubset(sizes)  # nosec B101


