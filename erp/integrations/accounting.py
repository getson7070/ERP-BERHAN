"""Stub for accounting system connector."""

import requests
import os

ACCOUNTING_URL = os.environ.get("ACCOUNTING_URL", "https://example.com/api")


def send_invoice(order: dict) -> bool:
    """Post an invoice payload to the external accounting system."""
    try:
        resp = requests.post(f"{ACCOUNTING_URL}/invoices", json=order, timeout=5)
        return resp.status_code == 200
    except requests.RequestException:
        return False


