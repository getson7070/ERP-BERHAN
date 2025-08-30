#!/usr/bin/env python3
"""Populate the database with large demo datasets for load testing."""
from __future__ import annotations

import os
from db import get_db
from erp.sql_compat import execute as safe_execute


def main() -> None:
    if os.environ.get("ALLOW_DEMO_SEEDING") != "1":
        raise SystemExit("Demo seeding disabled; set ALLOW_DEMO_SEEDING=1 to enable")
    items = int(os.environ.get("SEED_ITEMS", "10000"))
    users = int(os.environ.get("SEED_USERS", "1000"))
    conn = get_db()
    cur = conn.cursor()
    for i in range(items):
        sku = f"SKU{i}"
        name = f"Item{i}"
        safe_execute(
            cur,
            "INSERT INTO inventory_items (org_id, name, sku, quantity) VALUES (1, ?, ?, 0)",
            (name, sku),
        )
    for i in range(users):
        email = f"user{i}@example.com"
        safe_execute(
            cur,
            "INSERT INTO users (email, password, fs_uniquifier) VALUES (?, 'password', ?) ON CONFLICT(email) DO NOTHING",
            (email, f"uid{i}"),
        )
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
