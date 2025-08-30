from erp import create_app


def test_waf_blocks_script_tag():
    app = create_app()
    client = app.test_client()
    resp = client.get("/?q=<script>alert(1)</script>")
    assert resp.status_code == 400
