﻿import os, sqlite3, hashlib, datetime as dt
from typing import Iterable, Optional
from .metrics import AUDIT_CHAIN_BROKEN, AUDIT_CHAIN_BROKEN_TOTAL

def get_db():
    path = os.environ.get("DATABASE_PATH") or ":memory:"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def _hash_entry(prev_hash, user_id, org_id, action, details, created_at):
    s = f"{prev_hash or ""}|{user_id}|{org_id}|{action}|{details or ""}|{created_at}"
    return hashlib.sha256(s.encode()).hexdigest()

def log_audit(user_id: int, org_id: int, action: str, details: Optional[str]=None):
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, org_id INTEGER, action TEXT, details TEXT,
        prev_hash TEXT, hash TEXT, created_at TEXT
    )""")
    cur = conn.execute("SELECT hash FROM audit_logs ORDER BY id DESC LIMIT 1")
    prev = cur.fetchone()
    prev_hash = prev["hash"] if prev else None
    created_at = dt.datetime.utcnow().isoformat()
    new_hash = _hash_entry(prev_hash, user_id, org_id, action, details, created_at)
    conn.execute(
        "INSERT INTO audit_logs (user_id, org_id, action, details, prev_hash, hash, created_at) VALUES (?,?,?,?,?,?,?)",
        (user_id, org_id, action, details, prev_hash, new_hash, created_at),
    )
    conn.commit()
    conn.close()

def check_audit_chain(records: Optional[Iterable[sqlite3.Row]] = None) -> int:
    conn = None
    if records is None:
        conn = get_db()
        cur = conn.execute("SELECT id, user_id, org_id, action, details, prev_hash, hash, created_at FROM audit_logs ORDER BY id")
        records = list(cur.fetchall())
    breaks = 0
    prev_hash = None
    for r in records:
        calc = _hash_entry(prev_hash, r["user_id"], r["org_id"], r["action"], r["details"], r["created_at"])
        if calc != r["hash"]:
            breaks += 1
        prev_hash = r["hash"]
    if conn: conn.close()
    if breaks:
        AUDIT_CHAIN_BROKEN.inc(breaks)
        AUDIT_CHAIN_BROKEN_TOTAL.inc(breaks)
    return breaks
