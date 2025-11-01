import pytest
from pathlib import Path


def skip_if_browser_missing(browser: str, *, module_level: bool = False) -> None:
    """Skip tests when a Playwright browser isn't installed."""

    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser_type = getattr(p, browser)
            exec_path = browser_type.executable_path
            if not Path(exec_path).exists():
                raise FileNotFoundError(exec_path)
            browser_obj = browser_type.launch()
            browser_obj.close()
    except Exception as exc:  # pragma: no cover - skip logic
        pytest.skip(
            f"Playwright {browser} browser not installed or cannot launch: {exc}",
            allow_module_level=module_level,
        )


