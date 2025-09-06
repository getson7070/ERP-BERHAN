import pytest


def skip_if_browser_missing(browser: str, *, module_level: bool = False) -> None:
    """Skip tests when a Playwright browser isn't installed.

    Parameters
    ----------
    browser: str
        Name of the browser attribute on the Playwright object (e.g., "chromium", "firefox").
    module_level: bool, optional
        Whether the skip should occur at import time for the whole module.
    """
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    try:
        from pathlib import Path

        with sync_playwright() as p:
            exec_path = getattr(p, browser).executable_path
            if not Path(exec_path).is_file():
                raise FileNotFoundError(exec_path)
    except Exception as exc:  # pragma: no cover - skip logic
        pytest.skip(
            f"Playwright {browser} browser not installed: {exc}",
            allow_module_level=module_level,
        )
