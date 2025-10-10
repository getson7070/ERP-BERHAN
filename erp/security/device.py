# erp/security/device.py
from __future__ import annotations
from typing import Dict, Literal, Optional
from sqlalchemy import text
from flask import Request

Role = Literal["admin", "employee", "client"]

def read_device_id(req: Request) -> Optional[str]:
    """
    Order of precedence:
      1) 'X-Device-ID' header
      2) query string ?device=...
      3) cookie 'device'
    """
    did = req.headers.get("X-Device-ID")
    if not did:
        did = req.args.get("device")
    if not did:
        did = req.cookies.get("device")
    if did:
        did = did.strip()
    return did or None

def highest_role_for_device(bind, device_id: str) -> Optional[Role]:
    """
    Returns the highest role this device is authorized for,
    based on user->role rows in device_authorizations.
    Priority: admin > employee > client.
    """
    # One query gets distinct roles for the device
    rows = bind.execute(text("""
        SELECT DISTINCT u.role
        FROM device_authorizations da
        JOIN users u ON u.id = da.user_id
        WHERE da.device_id = :device AND COALESCE(da.allowed, true) = true
    """), dict(device=device_id)).fetchall()

    roles = { (r[0] or "").lower() for r in rows }
    if "admin" in roles:
        return "admin"
    if "employee" in roles:
        return "employee"
    if "client" in roles:
        return "client"
    return None

def compute_activation_for_device(bind, device_id: Optional[str]) -> Dict[str, bool]:
    """
    Decides which tiles are active for the incoming device.
    Rules from the user:
      - if allowed for admin -> all three active
      - else if allowed for employee -> employee + client
      - else (not allowed) -> client only
    """
    active = {"client": True, "employee": False, "admin": False}
    if not device_id:
        # No device info -> treat as not allowed (client only)
        return active

    top = highest_role_for_device(bind, device_id)
    if top == "admin":
        active.update({"employee": True, "admin": True})
    elif top == "employee":
        active.update({"employee": True})
    elif top == "client":
        # Explicit client allow doesn't change beyond default client-only,
        # but keep semantics consistent.
        pass
    # else None -> not allowed; client-only remains
    return active
