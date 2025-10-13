# erp/security_shim.py
import os
from flask import Request

def read_device_id(req: Request) -> str:
    return (
        req.headers.get("X-Device-ID")
        or req.cookies.get("device_id")
        or req.remote_addr
        or "unknown"
    )

def _as_bool(v: str | None, default=False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}

def compute_activation_for_device(device_id: str) -> dict:
    """
    Controls which tiles appear on the choose-login screen.
    Driven by env flags so you can flip without a code deploy.
    """
    return {
        "client":   _as_bool(os.getenv("ENABLE_CLIENT_LOGIN", "true"), True),
        "employee": _as_bool(os.getenv("ENABLE_EMPLOYEE_LOGIN", "false")),
        "admin":    _as_bool(os.getenv("ENABLE_ADMIN_LOGIN", "false")),
        "warehouse":_as_bool(os.getenv("ENABLE_WAREHOUSE", "false")),
    }
