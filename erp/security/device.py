# erp/security/device.py
from __future__ import annotations
from typing import Tuple
from flask import Request

def read_device_id(req: Request) -> str | None:
    """
    Read device identifiers from the request:
      - X-Device-Id header (preferred)
      - ?device= query parameter (fallback)
      - X-Serial-Number or ?serial= (optional hardware serial)
    Returns the first non-empty string, or None.
    """
    for key in ("X-Device-Id", "X-Serial-Number"):
        val = (req.headers.get(key) or "").strip()
        if val:
            return val
    for key in ("device", "serial"):
        val = (req.args.get(key) or "").strip()
        if val:
            return val
    return None

def compute_activation_for_device(req: Request) -> Tuple[bool, bool, bool]:
    """
    Returns (client_on, employee_on, admin_on) for choose_login.
    Rule:
      - Client tile: always ON (public)
      - If device is in allowlist for an employee user -> employee tile ON
      - If device is in allowlist for an admin user -> admin tile ON (and employee too)
    The actual allowlist check is done using DB in the route (kept simple here),
    or you can inject a service that resolves flags from DB by device id.
    """
    # This module only parses; the route decides with DB.
    device = read_device_id(req)
    # Defaults if we cannot identify device here.
    return (True, False, False)
