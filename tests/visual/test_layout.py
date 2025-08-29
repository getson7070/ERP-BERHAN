from pathlib import Path
import pytest

pytest.importorskip("playwright")
from playwright.sync_api import Page


def test_blank_page(page: Page):
    page.set_viewport_size({"width": 200, "height": 200})
    page.goto("about:blank")
    screenshot = page.screenshot()
    baseline = Path(__file__).with_name("blank.png")
    if not baseline.exists():
        baseline.write_bytes(screenshot)
        raise AssertionError("baseline created; rerun test")
    assert screenshot == baseline.read_bytes()  # nosec B101
