# erp/security.py
from __future__ import annotations

import hashlib
import os
from typing import Dict, Optional

from flask import Request

from .extensions import db
from .models import DeviceAuthorization  # device_id, role, user_id, allowed (bool)

# -----------------------------------------------------------------------------
# Optional encryption (lazy import so Alembic/env.py doesn't require the wheel)
# -----------------------------------------------------------------------------
def _fernet():
    from cryptography.fernet import Fernet  # lazy import to avoid build-time errors
    return Fernet

def _get_fernet_key() -> Optional[bytes]:
    """Derive/create a key from env. If not set, return None (no encryption)."""
    raw = os.getenv("DEVICE_SECRET_KEY") or os.getenv("FLASK_SECRET_KEY")
    if not raw:
        return None
    # Normalize to 32-byte base key for Fernet
    key = hashlib.sha256(raw.encode("utf-8")).digest()
    # Fernet expects urlsafe base64-encoded 32 bytes
    import base64
    return base64.urlsafe_b64encode(key)

def encrypt_device_id(device_id: str) -> str:
    key = _get_fernet_key()
    if not key:
        return device_id
    f = _fernet()(key)
    return f.encrypt(device_id.encode("utf-8")).decode("utf-8")

def decrypt_device_id(token: str) -> str:
    key = _get_fernet_key()
    if not key:
        return token
    f = _fernet()(key)
    try:
        return f.decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception:
        return token


# -----------------------------------------------------------------------------
# Device ID collection
# -----------------------------------------------------------------------------
POSSIBLE_HEADERS = (
    "X-Device-Id",
    "X-Serial-Number",
    "X-Client-Device",
    "X-Client-Id",
)

def _from_headers(req: Request) -> Optional[str]:
    for h in POSSIBLE_HEADERS:
        v = req.headers.get(h)
        if v:
            return v.strip()
    return None

def _from_query(req: Request) -> Optional[str]:
    # Allow ?device=… for quick manual testing
    for k in ("device", "dev", "serial", "sn", "mac"):
        v = req.args.get(k)
        if v:
            return v.strip()
    return None

def _from_cookies(req: Request) -> Optional[str]:
    v = req.cookies.get("device_id")
    return v.strip() if v else None

def _fingerprint(req: Request) -> str:
    """
    Last-resort fingerprint (public fallback): hash of UA + remote IP.
    Not used for enforcement — only to keep a stable value for anonymous clients.
    """
    ua = (req.headers.get("User-Agent") or "").strip()
    ip = (req.headers.get("X-Forwarded-For") or req.remote_addr or "").split(",")[0].strip()
    data = f"{ua}|{ip}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def read_device_id(req: Request) -> str:
    """
    Best-effort device identifier:
      1) Recognized headers (X-Device-Id / X-Serial-Number / …)
      2) Query string (?device=…)
      3) Cookie 'device_id'
      4) Fallback stable fingerprint (UA+IP)
    """
    for getter in (_from_headers, _from_query, _from_cookies):
        v = getter(req)
        if v:
            return v
    return _fingerprint(req)


# -----------------------------------------------------------------------------
# UI activation policy (what tiles to show on /choose_login)
# -----------------------------------------------------------------------------
def compute_activation_for_device(device_id: Optional[str]) -> Dict[str, bool]:
    """
    Returns flags consumed by templates:
      - show_client: always True (public)
      - show_employee: True if the device appears on any allowed employee or admin record
      - show_admin: True if the device appears on any allowed admin record
    """
    # Public default
    flags = dict(show_client=True, show_employee=False, show_admin=False)

    if not device_id:
        return flags

    # Normalize once (no encryption assumed in DB; if you store encrypted strings, call decrypt here)
    dev = str(device_id).strip()

    try:
        # Query only allowed=TRUE rows for this exact device_id
        rows = DeviceAuthorization.query.filter_by(device_id=dev, allowed=True).all()
    except Exception:
        # DB not reachable during some phases (e.g., early migrations) — keep defaults
        return flags

    if not rows:
        return flags

    # If any admin record is present -> full access
    if any((r.role or "").lower() == "admin" for r in rows):
        flags["show_employee"] = True
        flags["show_admin"] = True
        return flags

    # Else if any employee record is present -> client + employee
    if any((r.role or "").lower() == "employee" for r in rows):
        flags["show_employee"] = True
        return flags

    # Otherwise keep client only
    return flags
