from pathlib import Path


def test_service_worker_strips_auth_header():
    content = Path("static/js/sw.js").read_text()
    assert "Authorization" in content
    assert "headers.delete" in content
    assert "!request.headers.has('Authorization')" in content


def test_service_worker_replays_with_auth_header():
    content = Path("static/js/sw.js").read_text()
    assert "requestWillReplay" in content
    assert "headers.set('Authorization'" in content


