from __future__ import annotations
import hashlib, json, datetime as dt
from db import get_db

def _hash(prev_hash: str, rec: dict, secret: str="k") -> str:
    h = hashlib.sha256()
    h.update((prev_hash or "").encode())
    h.update(json.dumps(rec, sort_keys=True).encode())
    h.update(secret.encode())
    return h.hexdigest()

def log_audit(user_id: int, org_id: int, action: str, details: str | None = None, secret: str = "k"):
    conn = get_db()
    try:
        row = conn.execute("SELECT hash FROM audit_logs ORDER BY id DESC LIMIT 1").fetchone()
        prev = (row["hash"] if row and "hash" in row.keys() else (row[0] if row else "")) or ""
    except Exception:
        prev = ""
    rec = {"user_id": user_id, "org_id": org_id, "action": action, "details": details or ""}
    h = _hash(prev, rec, secret)
    conn.execute(
        "INSERT INTO audit_logs (user_id, org_id, action, details, prev_hash, hash, created_at) VALUES (?,?,?,?,?,?,?)",
        (user_id, org_id, action, details or "", prev, h, dt.datetime.utcnow().isoformat()),
    )
    conn.commit()
    return h
