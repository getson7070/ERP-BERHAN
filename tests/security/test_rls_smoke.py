import os

import pytest

try:
    import psycopg2
except ModuleNotFoundError:  # pragma: no cover - dependency optional
    psycopg2 = None

DATABASE_URL = os.environ.get("POSTGRES_URI")
if not DATABASE_URL or psycopg2 is None:
    pytest.skip("PostgreSQL not available", allow_module_level=True)


def test_rls_blocks_cross_org():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SET erp.org_id = 1")
            cur.execute("INSERT INTO audit_logs (org_id, action) VALUES (1, 'x')")
            cur.execute("SET erp.org_id = 2")
            cur.execute("SELECT COUNT(*) FROM audit_logs WHERE org_id = 1")
            assert cur.fetchone()[0] == 0
            conn.rollback()


