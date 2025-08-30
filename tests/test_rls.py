import uuid

import pytest
from db import get_db


def _connect_or_skip():
    try:
        conn = get_db()
    except Exception as exc:  # pragma: no cover - skip if DB unavailable
        pytest.skip(f"database not available: {exc}")
    if getattr(conn, "_dialect", None).name != "postgresql":
        pytest.skip("RLS requires PostgreSQL")
    return conn


def test_rls_blocks_cross_tenant():
    conn = _connect_or_skip()
    cur = conn.cursor()
    cust_a, cust_b = str(uuid.uuid4()), str(uuid.uuid4())
    # Insert order for org 1
    cur.execute("SET erp.org_id = %s", (1,))
    cur.execute(
        "INSERT INTO orders (org_id, customer, status) VALUES (%s, %s, %s)",
        (1, cust_a, "pending"),
    )
    # Insert order for org 2
    cur.execute("SET erp.org_id = %s", (2,))
    cur.execute(
        "INSERT INTO orders (org_id, customer, status) VALUES (%s, %s, %s)",
        (2, cust_b, "pending"),
    )
    conn.commit()
    # Verify org 1 cannot see org 2's order
    cur.execute("SET erp.org_id = %s", (1,))
    cur.execute(
        "SELECT customer FROM orders WHERE customer IN (%s, %s) ORDER BY customer",
        (cust_a, cust_b),
    )
    assert cur.fetchall() == [(cust_a,)]
    # Verify org 2 cannot see org 1's order
    cur.execute("SET erp.org_id = %s", (2,))
    cur.execute(
        "SELECT customer FROM orders WHERE customer IN (%s, %s) ORDER BY customer",
        (cust_a, cust_b),
    )
    assert cur.fetchall() == [(cust_b,)]
    # Clean up
    cur.execute("SET erp.org_id = %s", (1,))
    cur.execute("DELETE FROM orders WHERE customer = %s", (cust_a,))
    cur.execute("SET erp.org_id = %s", (2,))
    cur.execute("DELETE FROM orders WHERE customer = %s", (cust_b,))
    conn.commit()
    cur.close()
    conn.close()
