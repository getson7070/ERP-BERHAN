# erp/security_shim.py
from flask import Request

def read_device_id(req: Request) -> str:
    return (
        req.headers.get("X-Device-ID")
        or req.cookies.get("device_id")
        or req.remote_addr
        or "unknown"
    )

def compute_activation_for_device(device_id: str) -> dict:
    """
    Keys used by templates:
      - client, employee, admin, warehouse (all booleans)
    """
    return {
        "client": True,
        "employee": True,
        "admin": True,
        "warehouse": False,  # hide unless you really want to expose it
    }
