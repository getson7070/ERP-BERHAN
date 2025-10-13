# erp/security/device.py
from __future__ import annotations
from typing import Dict
from flask import Request

def read_device_id(request: Request) -> str:
    # minimal, deterministic id using headers
    h = request.headers
    raw = f"{h.get('X-Forwarded-For','?')}|{h.get('User-Agent','?')}"
    # short hash for privacy
    import hashlib
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

def compute_activation_for_device(device_id: str, config) -> Dict[str, bool]:
    # Feature switches come from env/config.
    return {
        "client": str(config.get("ENABLE_CLIENT_LOGIN", "true")).lower() == "true",
        "employee": str(config.get("ENABLE_EMPLOYEE_LOGIN", "false")).lower() == "true",
        "admin": str(config.get("ENABLE_ADMIN_LOGIN", "false")).lower() == "true",
    }
