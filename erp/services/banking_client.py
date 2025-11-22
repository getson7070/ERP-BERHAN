"""Banking client wrapper with circuit breaker protection."""
from __future__ import annotations

import os
from typing import Any

import requests

from erp.reliability import apply_chaos_to_external_calls, close_incident, get_breaker, open_incident

BANK_BREAKER = get_breaker("banking")


def banking_ping() -> bool:
    """Lightweight ping; returns False if the breaker is open or ping fails."""

    if not BANK_BREAKER.allow():
        open_incident(None, "banking", {"reason": "open_circuit"})
        return False

    url = os.getenv("BANKING_HEALTH_URL") or os.getenv("BANK_API_HEALTH")
    if not url:
        return True  # no external dependency configured

    apply_chaos_to_external_calls()

    try:
        resp = requests.get(url, timeout=3)
        resp.raise_for_status()
        BANK_BREAKER.record_success()
        close_incident(None, "banking")
        return True
    except Exception:
        BANK_BREAKER.record_failure()
        open_incident(None, "banking", {"url": url, "reason": "ping_failed"})
        return False


def fetch_statement(account_id: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if not BANK_BREAKER.allow():
        open_incident(None, "banking", {"reason": "open_circuit"})
        return {"ok": False, "error": "banking_unavailable"}

    base_url = os.getenv("BANK_API_BASE_URL")
    if not base_url:
        return {"ok": False, "error": "bank_api_base_url_not_configured"}

    apply_chaos_to_external_calls()

    try:
        resp = requests.get(
            f"{base_url.rstrip('/')}/accounts/{account_id}/statement",
            params=params or {},
            timeout=8,
        )
        resp.raise_for_status()
        BANK_BREAKER.record_success()
        close_incident(None, "banking")
        return {"ok": True, "data": resp.json()}
    except Exception as exc:
        BANK_BREAKER.record_failure()
        open_incident(None, "banking", {"reason": "fetch_failed", "error": str(exc)})
        return {"ok": False, "error": str(exc)}
