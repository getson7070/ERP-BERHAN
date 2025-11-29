import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app


def test_healthz_allowlisted_under_strict_boundaries():
    app = create_app()
    app.config.update(
        TESTING=False,
        STRICT_ORG_BOUNDARIES=True,
    )
    client = app.test_client()

    response = client.get("/healthz")

    assert response.status_code == 200
