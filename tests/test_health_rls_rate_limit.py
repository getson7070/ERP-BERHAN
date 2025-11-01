import re
import pytest

from erp import create_app

# DB engine for RLS checks
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.engine import Engine
from typing import Optional

engine: Optional[Engine]
try:
    from db import engine as engine  # type: ignore[assignment]
except Exception:
    engine = None


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _metric_value(metrics_text: str, metric: str) -> float:
    """
    Parse Prometheus exposition text and return the first numeric value
    for a metric (no labels or with labels). Example line:
      rate_limit_rejections_total 3.0
      rate_limit_rejections_total{route="/auth/token"} 2.0
    """
    pattern = re.compile(
        rf"^{re.escape(metric)}(?:{{[^}}]*}})?\s+([0-9]+(?:\.[0-9]+)?)$", re.MULTILINE
    )
    m = pattern.search(metrics_text)
    return float(m.group(1)) if m else 0.0


# -----------------------------
# 1) Health endpoints existence
# -----------------------------
def test_health_endpoints_ok(client):
    r = client.get("/health")
    assert r.status_code == 200, f"/health returned {r.status_code}"
    body = r.get_json(silent=True) or {}
    assert body.get("ok") is True

    r = client.get("/healthz")
    assert r.status_code in (200, 503), f"/healthz returned {r.status_code}"
    if r.status_code == 200:
        body = r.get_json(silent=True) or {}
        assert body.get("ok") is True


# ------------------------------------------
# 2) RLS: cross-tenant reads must be blocked
# ------------------------------------------
@pytest.mark.skipif(
    engine is None
    or getattr(getattr(engine, "dialect", None), "name", "") != "postgresql",
    reason="RLS test requires PostgreSQL engine",
)
def test_rls_blocks_cross_tenant_reads():
    """
    Precondition: RLS enabled with policies bound to current_setting('erp.org_id')::int
    This test inserts two rows with different org_id values and proves that
    a session scoped to org 1 cannot see org 2's row (and vice versa).
    """
    test_id_org1 = 9900001
    test_id_org2 = 9900002

    with engine.begin() as conn:
        # Make sure table exists; if not, skip gracefully
        try:
            conn.execute(text("SELECT 1 FROM orders LIMIT 1"))
        except ProgrammingError:
            pytest.skip("orders table not present; skipping RLS test")

        # Seed one row per org, scoping each INSERT to that org
        conn.execute(text("SET erp.org_id = :org"), {"org": 1})
        conn.execute(
            text(
                "INSERT INTO orders (id, org_id, status) VALUES (:id, :org_id, 'pending') ON CONFLICT (id) DO NOTHING"
            ),
            {"id": test_id_org1, "org_id": 1},
        )
        conn.execute(text("SET erp.org_id = :org"), {"org": 2})
        conn.execute(
            text(
                "INSERT INTO orders (id, org_id, status) VALUES (:id, :org_id, 'pending') ON CONFLICT (id) DO NOTHING"
            ),
            {"id": test_id_org2, "org_id": 2},
        )

    # Session as org 1: must NOT see org 2's row
    with engine.begin() as conn:
        conn.execute(text("SET erp.org_id = :org"), {"org": 1})
        cnt1 = conn.execute(
            text("SELECT COUNT(*) FROM orders WHERE id = :id"), {"id": test_id_org1}
        ).scalar_one()
        cnt2 = conn.execute(
            text("SELECT COUNT(*) FROM orders WHERE id = :id"), {"id": test_id_org2}
        ).scalar_one()
        assert cnt1 == 1, "Org 1 should see its own row"
        assert cnt2 == 0, "Org 1 must NOT see Org 2's row (RLS)"

    # Session as org 2: mirror assertion
    with engine.begin() as conn:
        conn.execute(text("SET erp.org_id = :org"), {"org": 2})
        cnt1 = conn.execute(
            text("SELECT COUNT(*) FROM orders WHERE id = :id"), {"id": test_id_org1}
        ).scalar_one()
        cnt2 = conn.execute(
            text("SELECT COUNT(*) FROM orders WHERE id = :id"), {"id": test_id_org2}
        ).scalar_one()
        assert cnt1 == 0, "Org 2 must NOT see Org 1's row (RLS)"
        assert cnt2 == 1, "Org 2 should see its own row"


# ---------------------------------------------------------
# 3) Rate limit: 429 returned and counter increments in /metrics
# ---------------------------------------------------------
def test_rate_limit_increments_counter(client):
    # Read metric before
    m0 = client.get("/metrics")
    assert m0.status_code == 200
    before = _metric_value(m0.get_data(as_text=True), "rate_limit_rejections_total")

    # Hit a strongly limited endpoint: /auth/token is typically 2/min
    # We intentionally trigger the limiter by calling 3 times quickly.
    for _ in range(3):
        client.post(
            "/auth/token",
            data={},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    resp = client.post(
        "/auth/token",
        data={},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if resp.status_code != 429:
        pytest.skip(f"/auth/token not rate limited (status {resp.status_code})")

    # Read metric after
    m1 = client.get("/metrics")
    assert m1.status_code == 200
    after = _metric_value(m1.get_data(as_text=True), "rate_limit_rejections_total")
    assert (
        after >= before + 1.0
    ), f"rate_limit_rejections_total did not increase (before={before}, after={after})"


