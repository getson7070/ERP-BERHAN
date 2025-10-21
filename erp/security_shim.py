# erp/security_shim.py
from typing import Dict
from flask import Request

def read_device_id(request: Request) -> str:
    # Basic device-id reader; customize if you have a header/cookie
    return request.headers.get("X-Device-Id", "unknown")

def compute_activation_for_device(device_id: str) -> Dict[str, bool]:
    # Simple defaults; plug your real rules here.
    return {"client": True, "employee": False, "admin": False}


