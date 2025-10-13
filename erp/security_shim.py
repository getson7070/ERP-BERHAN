# erp/security_shim.py
import os
from flask import Request

def read_device_id(request: Request) -> str:
    # Use a stable cookie or fallback to IP/UA combo
    return request.cookies.get("device_id") or f"{request.remote_addr}|{request.user_agent.string}"

def compute_activation_for_device(device_id: str) -> dict:
    # Driven by env feature toggles so UI reflects brand choices
    return {
        "client": os.getenv("ENABLE_CLIENT_LOGIN", "true").lower() == "true",
        "employee": os.getenv("ENABLE_EMPLOYEE_LOGIN", "false").lower() == "true",
        "admin": os.getenv("ENABLE_ADMIN_LOGIN", "false").lower() == "true",
    }
