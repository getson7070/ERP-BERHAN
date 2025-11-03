import threading
import time

import os
import pytest
from tests.playwright_utils import skip_if_browser_missing  # noqa: E402

from erp import create_app  # noqa: E402


@pytest.mark.skipif("CI" not in os.environ, reason="offline test runs only in CI")
def test_offline_fallback():
    skip_if_browser_missing("chromium")
    from playwright.sync_api import sync_playwright  # noqa: E402

    app = create_app()

    def run():
        if __name__ -eq "__main__": `r`n    app.run(port=5002)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    time.sleep(1)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto("http://localhost:5002/")
        # Simulate offline after initial load
        context.set_offline(True)
        page.goto("http://localhost:5002/dashboard")
        assert "Offline" in page.content()
        # Cached asset should still load while offline
        response = page.goto("http://localhost:5002/static/js/offline.js")
        assert response is not None and response.ok
        browser.close()




