"""Append-only audit logging helpers."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from flask import has_request_context, request
from flask_login import current_user

from erp.extensions import db
from erp.models import AuditLog
from erp.services.audit_crypto import encrypt_payload

DEFAULT_SENSITIVE_KEYS: set[str] = {
    "password",
    "totp_secret",
    "token",
    "otp",
    "email",
    "phone",
    "bank_account",
    "tin",
    "national_id",
}


def write_audit_log(
    *,
    org_id: int,
    module: str,
    action: str,
    actor_id: int | None = None,
    actor_type: str = "user",
    entity_type: str | None = None,
    entity_id: int | None = None,
    severity: str = "info",
    metadata: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    sensitive_keys: set[str] | None = None,
    request_id: str | None = None,
    commit: bool = False,
) -> AuditLog:
    """Insert an append-only audit row with optional encrypted payload."""

    actor = actor_id if actor_id is not None else getattr(current_user, "id", None)
    ip_addr = None
    user_agent = None
    req_id = request_id
    if has_request_context():
        ip_addr = request.headers.get("X-Forwarded-For") or request.remote_addr
        user_agent = request.headers.get("User-Agent")
        req_id = req_id or request.headers.get("X-Request-Id")

    sensitive = sensitive_keys or DEFAULT_SENSITIVE_KEYS
    encrypted_payload = encrypt_payload(payload or {}, sensitive) if payload else None

    entry = AuditLog(
        org_id=org_id,
        user_id=actor,
        actor_id=actor,
        actor_type=actor_type,
        module=module,
        action=action,
        severity=severity,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata or {},
        payload_encrypted=encrypted_payload,
        ip_address=ip_addr,
        user_agent=user_agent,
        request_id=req_id,
        created_at=datetime.now(UTC),
    )
    db.session.add(entry)
    if commit:
        db.session.commit()
    return entry
