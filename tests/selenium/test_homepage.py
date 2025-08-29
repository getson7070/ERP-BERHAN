import threading
import time
import os

import pytest

pytest.importorskip("selenium.webdriver")
pytest.importorskip("webdriver_manager")

import selenium.webdriver as webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402
from webdriver_manager.chrome import ChromeDriverManager  # noqa: E402

from erp import create_app  # noqa: E402


@pytest.mark.skipif("CI" not in os.environ, reason="Selenium smoke only runs in CI")
def test_homepage_loads(tmp_path):
    app = create_app()

    def run():
        app.run(port=5001)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    time.sleep(1)

    options = Options()
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
