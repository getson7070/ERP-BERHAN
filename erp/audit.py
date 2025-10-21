"""
Append-only audit log with hash chaining.
"""
from __future__ import annotations
import hashlib, json, importlib
from dataclasses import dataclass, asdict
from typing import List, Optional

def _hash_record(payload: dict, prev_hash: str | None) -> str:
    m = hashlib.sha256()
    if prev_hash:
        m.update(prev_hash.encode("utf-8"))
    # canonicalize
    m.update(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return m.hexdigest()

@dataclass
class AuditRecord:
    action: str
    user_id: str
    details: dict | None = None
    prev_hash: str | None = None
    hash: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

def log_audit(action: str, user_id: str, details: Optional[dict] = None, prev_hash: Optional[str] = None) -> AuditRecord:
    payload = {"action": action, "user_id": user_id, "details": details or {}}
    h = _hash_record(payload, prev_hash)
    return AuditRecord(action=action, user_id=user_id, details=details or {}, prev_hash=prev_hash, hash=h)

def check_audit_chain(records: List[AuditRecord]) -> bool:
    if not records:
        return True
    last = None
    ok = True
    for rec in records:
        expected = _hash_record({"action": rec.action, "user_id": rec.user_id, "details": rec.details or {}}, rec.prev_hash)
        if rec.hash != expected:
            ok = False
            break
        last = rec
    if not ok:
        # bump global exported counter on erp module if available
        try:
            erp = importlib.import_module("erp")
            # increment int-like flag
            setattr(erp, "AUDIT_CHAIN_BROKEN", getattr(erp, "AUDIT_CHAIN_BROKEN", 0) + 1)
        except Exception:
            pass
    return ok