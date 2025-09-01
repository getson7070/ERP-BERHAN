import uuid
import pytest
import psycopg2

from db import get_db


def _connect_or_skip():
    try:
        conn = get_db()
    except Exception as exc:  # pragma: no cover - skip if DB unavailable
        pytest.skip(f"database not available: {exc}")
    if getattr(conn, "_dialect", None).name != "postgresql":
        pytest.skip("RLS requires PostgreSQL")
    return conn


def test_cross_tenant_insert_blocked():
    conn = _connect_or_skip()
    cur = conn.cursor()
    cur.execute("SET erp.org_id = %s", (1,))
    with pytest.raises(psycopg2.errors.InsufficientPrivilege):
        cur.execute(
            "INSERT INTO orders (org_id, customer, status) VALUES (%s, %s, %s)",
            (2, str(uuid.uuid4()), "pending"),
        )
    cur.close()
    conn.close()
