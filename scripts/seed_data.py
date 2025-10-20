#!/usr/bin/env python3
"""Populate the database with large demo datasets for load testing."""
from __future__ import annotations

import os
from db import get_db
from erp.sql_compat import execute as safe_execute
from erp.utils import hash_password


def main() -> None:
    if os.environ.get("SEED_DEMO_DATA") != "1" or os.environ.get("ENV") == "production":
        raise SystemExit(
            "Demo seeding disabled; set SEED_DEMO_DATA=1 and ENV!=production to enable"
        )
    items = int(os.environ.get("SEED_ITEMS", "10000"))
    users = int(os.environ.get("SEED_USERS", "1000"))
    password_plain = os.environ.get("SEED_USER_PASSWORD")
    if not password_plain:
        raise SystemExit(
            "SEED_USER_PASSWORD environment variable required for user seeding"
        )
    password_hash = hash_password(password_plain)
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
            "INSERT INTO users (email, password, fs_uniquifier) VALUES (?, ?, ?) ON CONFLICT(email) DO NOTHING",
            (email, password_hash, f"uid{i}"),
        )
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()


