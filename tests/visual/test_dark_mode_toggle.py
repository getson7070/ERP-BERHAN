from pathlib import Path
import pytest

pytest.importorskip("playwright")
from tests.playwright_utils import skip_if_browser_missing  # noqa: E402

skip_if_browser_missing("chromium", module_level=True)
pytest.importorskip("pytest_playwright")
from playwright.sync_api import Page  # noqa: E402

HTML = """
<!DOCTYPE html>
<html lang='en' data-bs-theme='light'>
<head>
  <meta charset='UTF-8'>
  <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>
</head>
<body>
  <button id='toggle' class='btn btn-secondary'>Toggle</button>
  <script>
    const btn = document.getElementById('toggle');
    btn.addEventListener('click', () => {
      const html = document.documentElement;
      const theme = html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-bs-theme', theme);
    });
  </script>
</body>
</html>
"""


def test_dark_mode_toggle(page: Page) -> None:
    page.set_viewport_size({"width": 200, "height": 200})
    page.set_content(HTML)
    page.click("#toggle")
    screenshot = page.screenshot()
    baseline = Path(__file__).with_name("dark_mode.png")
    if not baseline.exists():
        baseline.write_bytes(screenshot)
        raise AssertionError("baseline created; rerun test")
    assert screenshot == baseline.read_bytes()  # nosec B101


