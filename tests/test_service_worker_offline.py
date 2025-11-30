# tests/test_service_worker_offline.py
"""
PWA / service worker sanity tests for ERP-BERHAN.

These tests do NOT attempt a full offline simulation; instead, they
assert that the key PWA endpoints exist and respond with HTTP 200:

- /static/manifest.webmanifest
- /static/register-sw.js
- /static/service-worker.js (if present)

They are guarded with pytest.importorskip("requests") so they do not
break the rest of the test suite if requests is not installed.
"""

import os

import pytest

requests = pytest.importorskip("requests")


BASE_URL = os.environ.get("ERP_BASE_URL", "http://localhost:18000")


def _get(path: str):
    url = BASE_URL.rstrip("/") + path
    resp = requests.get(url, timeout=5)
    return resp


def test_manifest_exists_and_is_json():
    resp = _get("/static/manifest.webmanifest")
    assert resp.status_code == 200, "PWA manifest should exist at /static/manifest.webmanifest"
    # Content type often "application/manifest+json" or "application/json"
    ctype = resp.headers.get("Content-Type", "")
    assert "json" in ctype.lower()


def test_register_sw_js_exists():
    resp = _get("/static/register-sw.js")
    assert resp.status_code == 200, "register-sw.js should exist at /static/register-sw.js"
    assert "serviceWorker" in resp.text or "navigator" in resp.text


def test_service_worker_file_if_present():
    """If the service-worker.js endpoint exists, it should return 200.

    We don't fail the whole test suite if it's missing entirely, but if it
    does exist we expect a 200.
    """
    resp = _get("/static/service-worker.js")
    if resp.status_code == 404:
        pytest.skip("No /static/service-worker.js found; skipping SW body check")
    assert resp.status_code == 200
    assert "self.addEventListener" in resp.text or "caches.open" in resp.text
