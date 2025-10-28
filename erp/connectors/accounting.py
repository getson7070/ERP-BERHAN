"""Module: connectors/accounting.py — audit-added docstring. Refine with precise purpose when convenient."""
import requests


def push_invoice(data: dict, endpoint: str):
    """Send invoice data to an external accounting system."""
    response = requests.post(endpoint, json=data, timeout=5)
    response.raise_for_status()
    return response.json()



