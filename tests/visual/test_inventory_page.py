from pathlib import Path
import pytest

pytest.importorskip("playwright")
from tests.playwright_utils import skip_if_browser_missing  # noqa: E402

skip_if_browser_missing("chromium", module_level=True)
pytest.importorskip("pytest_playwright")
from playwright.sync_api import Page  # noqa: E402

HTML = """
<!DOCTYPE html>
<html lang='en'>
<head>
  <meta charset='UTF-8'>
  <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>
  <title>Inventory</title>
</head>
<body>
  <div class='container py-5'>
    <h1>Inventory</h1>
    <table class='table table-striped'></table>
  </div>
</body>
</html>
"""


def test_inventory_page(page: Page):
    page.set_viewport_size({"width": 800, "height": 600})
    page.set_content(HTML)
    screenshot = page.screenshot()
    baseline = Path(__file__).with_name("inventory.png")
    if not baseline.exists():
        baseline.write_bytes(screenshot)
        raise AssertionError("baseline created; rerun test")
    assert screenshot == baseline.read_bytes()  # nosec B101
