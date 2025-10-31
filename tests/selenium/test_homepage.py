import threading
import time
import os

import pytest

pytest.importorskip("selenium.webdriver")
pytest.importorskip("webdriver_manager")

import selenium.webdriver as webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options as ChromeOptions  # noqa: E402
from selenium.webdriver.firefox.options import Options as FirefoxOptions  # noqa: E402
from selenium.webdriver.edge.options import Options as EdgeOptions  # noqa: E402
from selenium.webdriver.safari.options import Options as SafariOptions  # noqa: E402
from webdriver_manager.chrome import ChromeDriverManager  # noqa: E402
from webdriver_manager.firefox import GeckoDriverManager  # noqa: E402

from erp import create_app  # noqa: E402


@pytest.mark.skipif("CI" not in os.environ, reason="Selenium smoke only runs in CI")
def test_homepage_loads(tmp_path):
    app = create_app()

    def run():
        app.run(port=5001)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    time.sleep(1)

    browser = os.environ.get("BROWSER", "chrome")
    if browser == "firefox":
        options = FirefoxOptions()
        options.add_argument("--headless")
        try:
            driver = webdriver.Firefox(
                executable_path=GeckoDriverManager().install(), options=options
            )
        except Exception as exc:  # pragma: no cover
            pytest.skip(f"Firefox not available: {exc}")
    elif browser == "safari":
        remote_url = os.environ.get("SELENIUM_REMOTE_URL")
        if not remote_url:
            pytest.skip("Safari requires SELENIUM_REMOTE_URL")
        options = SafariOptions()
        try:
            driver = webdriver.Remote(command_executor=remote_url, options=options)
        except Exception as exc:  # pragma: no cover
            pytest.skip(f"Safari not available: {exc}")
    elif browser == "edge":
        remote_url = os.environ.get("SELENIUM_REMOTE_URL")
        if not remote_url:
            pytest.skip("Edge requires SELENIUM_REMOTE_URL")
        options = EdgeOptions()
        options.use_chromium = True
        options.add_argument("--headless")
        try:
            driver = webdriver.Remote(command_executor=remote_url, options=options)
        except Exception as exc:  # pragma: no cover
            pytest.skip(f"Edge not available: {exc}")
    else:
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        try:
            driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        except Exception as exc:  # pragma: no cover - depends on CI environment
            pytest.skip(f"Chrome not available: {exc}")
    try:
        driver.get("http://localhost:5001/")
        assert "BERHAN" in driver.title  # nosec B101
    finally:
        driver.quit()



