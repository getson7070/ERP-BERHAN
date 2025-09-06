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
        with sync_playwright() as p:
            # Attempt to launch the browser to ensure that the executable and
            # all required system dependencies are present. Immediately close
            # the browser to avoid side effects.
            browser_obj = getattr(p, browser).launch()
            browser_obj.close()
    except Exception as exc:  # pragma: no cover - skip logic
        pytest.skip(
            f"Playwright {browser} browser not installed or cannot launch: {exc}",
            allow_module_level=module_level,
        )
