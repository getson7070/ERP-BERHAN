from werkzeug.exceptions import Forbidden


def test_not_found_html(client):
    resp = client.get("/definitely-missing", headers={"Accept": "text/html"})
    assert resp.status_code == 404
    assert b"Page not found" in resp.data
    assert b"Help Center" in resp.data


def test_not_found_json(client):
    resp = client.get("/definitely-missing", headers={"Accept": "application/json"})
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "page_not_found"


def test_forbidden_html(app):
    with app.test_request_context("/secure", headers={"Accept": "text/html"}):
        resp, status = app.handle_user_exception(Forbidden())
        assert status == 403
        body = resp if isinstance(resp, (bytes, str)) else resp.data
        if isinstance(body, str):
            body = body.encode()
        assert b"Access denied" in body


def test_forbidden_json(app):
    with app.test_request_context("/secure", headers={"Accept": "application/json"}):
        resp, status = app.handle_user_exception(Forbidden())
        assert status == 403
        assert resp.get_json()["error"] == "access_denied"


def test_server_error_html(app):
    with app.test_request_context("/boom", headers={"Accept": "text/html"}):
        app.config["PROPAGATE_EXCEPTIONS"] = False
        resp = app.handle_exception(RuntimeError("boom"))
        assert resp.status_code == 500
        assert b"Something went wrong" in resp.data
