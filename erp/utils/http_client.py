"""Module: utils/http_client.py — audit-added docstring. Refine with precise purpose when convenient."""
# erp/utils/http_client.py
from __future__ import annotations
import httpx
from erp.utils.retries import retry_external, ExternalError
from erp.utils.circuit import breaker

# Shared HTTPX client; consider AsyncClient if you run async.
_client = httpx.Client(timeout=httpx.Timeout(5.0, read=10.0))

@retry_external
@breaker
def get_json(url: str, *, headers: dict | None = None) -> dict:
    try:
        r = _client.get(url, headers=headers)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise ExternalError(str(e)) from e

@retry_external
@breaker
def post_json(url: str, payload: dict, *, headers: dict | None = None) -> dict:
    try:
        r = _client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise ExternalError(str(e)) from e



