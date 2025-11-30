# tests/selenium/test_homepage.py
"""
Basic Selenium smoke test for ERP-BERHAN.

This test is intentionally lightweight:
- It checks that the homepage is reachable.
- It verifies that unauthenticated access redirects to the login page.
- It confirms the login form is rendered.

It is guarded by pytest.importorskip so the rest of the test suite
does not fail if Selenium is not installed in the environment.
"""

import os
import time

import pytest

selenium = pytest.importorskip("selenium")
from selenium import webdriver  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.chrome.options import Options as ChromeOptions  # type: ignore


BASE_URL = os.environ.get("ERP_BASE_URL", "http://localhost:18000")


@pytest.fixture(scope="session")
def browser():
    """Provide a minimal Chrome WebDriver instance.

    If the driver cannot be started (e.g. binary missing), the test
    will be skipped instead of failing the whole suite.
    """
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=options)
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Could not start Chrome driver: {exc}")

    yield driver
    driver.quit()


def test_home_redirects_to_login(browser):
    """Unauthenticated '/' should redirect to the login page."""
    browser.get(BASE_URL + "/")
    # Give a tiny bit of time for redirect
    time.sleep(0.5)

    current_url = browser.current_url
    # We expect something like .../auth/login?next=...
    assert "/auth/login" in current_url


def test_login_page_renders(browser):
    """Login page should render and contain the email/password fields."""
    browser.get(BASE_URL + "/auth/login")

    # Basic sanity checks on the form
    email_inputs = browser.find_elements(By.NAME, "email")
    password_inputs = browser.find_elements(By.NAME, "password")

    assert email_inputs, "Expected an email input on the login page"
    assert password_inputs, "Expected a password input on the login page"

    # CSRF token should be present as a hidden field
    csrf_inputs = browser.find_elements(By.NAME, "csrf_token")
    assert csrf_inputs, "Expected a CSRF token input on the login page"
