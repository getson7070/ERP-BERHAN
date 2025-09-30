# erp/audit.py
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .constants import AUDIT_CHAIN_BROKEN  # import locally to avoid package cycles

_log = logging.getLogger("audit")

def log_audit(event: str, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Non-blocking audit logger.
    Writes a structured JSON line to the 'audit' logger. If your existing routes
    also persist audits to DB/Redis, you can call those here – but this must never
    block or import the application package (to avoid boot cycles).
    """
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "user_id": user_id,
        "details": details or {},
    }
    try:
        _log.info(json.dumps(payload, ensure_ascii=False))
    except Exception:
        # Absolutely never allow audit to crash the app
        pass

__all__ = ["log_audit", "AUDIT_CHAIN_BROKEN"]
