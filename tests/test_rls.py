import os

import pytest

try:
    import psycopg2
except ModuleNotFoundError:  # pragma: no cover - dependency optional
    psycopg2 = None

DATABASE_URL = os.environ.get("POSTGRES_URI")
if not DATABASE_URL or psycopg2 is None:
    pytest.skip("PostgreSQL not available", allow_module_level=True)


def test_rls_isolation(tmp_path):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SET erp.org_id = 1")
            cur.execute(
                """
                INSERT INTO hr_recruitment (org_id, candidate_name, position, applied_on, status)
                VALUES (1, 'Alice', 'Dev', now(), 'applied')
                """
            )
            cur.execute("SET erp.org_id = 2")
            cur.execute("SELECT COUNT(*) FROM hr_recruitment WHERE org_id = 1")
            assert cur.fetchone()[0] == 0
            conn.rollback()


