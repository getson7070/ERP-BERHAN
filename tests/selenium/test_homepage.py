import threading
import time
import os

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from erp import create_app


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
        assert "BERHAN" in driver.title
    finally:
        driver.quit()
