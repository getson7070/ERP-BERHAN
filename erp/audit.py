import hashlib
import json
from datetime import datetime, timezone

def _hash_entry(prev_hash: str, entry: dict) -> str:
    payload = json.dumps({**entry, "prev": prev_hash}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def log_audit(actor: str, action: str, details: dict | None = None, prev_hash: str = "") -> dict:
    entry = {
        "actor": actor,
        "action": action,
        "details": details or {},
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    h = _hash_entry(prev_hash, entry)
    entry["hash"] = h
    entry["prev_hash"] = prev_hash
    return entry

def check_audit_chain(entries: list[dict]) -> bool:
    prev = ""
    for e in entries:
        expected = _hash_entry(prev, {k: e[k] for k in ("actor","action","details","ts")})
        if e.get("hash") != expected or e.get("prev_hash","") != prev:
            return False
        prev = e["hash"]
    return True
