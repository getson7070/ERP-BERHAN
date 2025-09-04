from pathlib import Path
import pytest

pytest.importorskip("playwright")
from tests.playwright_utils import skip_if_browser_missing  # noqa: E402

skip_if_browser_missing("chromium", module_level=True)
pytest.importorskip("pytest_playwright")
from playwright.sync_api import Page  # noqa: E402


def test_blank_page(page: Page):
    page.set_viewport_size({"width": 200, "height": 200})
    page.goto("about:blank")
    screenshot = page.screenshot()
    baseline = Path(__file__).with_name("blank.png")
    if not baseline.exists():
        baseline.write_bytes(screenshot)
        raise AssertionError("baseline created; rerun test")
    assert screenshot == baseline.read_bytes()  # nosec B101
