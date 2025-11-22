from __future__ import annotations

from datetime import datetime
import secrets

from erp.extensions import db
from erp.models import UserSession


def record_session(org_id: int, user_id: int, session_id: str) -> UserSession:
    record = UserSession.query.filter_by(org_id=org_id, session_id=session_id).first()
    if record is None:
        record = UserSession(org_id=org_id, user_id=user_id, session_id=session_id)
        db.session.add(record)
    record.last_seen_at = datetime.utcnow()
    db.session.commit()
    return record


def revoke_all_sessions_for_user(user_id: int, revoked_by_id: int | None = None) -> None:
    rows = UserSession.query.filter_by(user_id=user_id, revoked_at=None).all()
    now = datetime.utcnow()
    for row in rows:
        row.revoked_at = now
        row.revoked_by_id = revoked_by_id
    db.session.commit()


def revoke_session(org_id: int, session_id: str, revoked_by_id: int | None = None) -> None:
    record = UserSession.query.filter_by(org_id=org_id, session_id=session_id, revoked_at=None).first()
    if record:
        record.revoked_at = datetime.utcnow()
        record.revoked_by_id = revoked_by_id
        db.session.commit()


def touch_session(org_id: int, session_id: str) -> None:
    record = UserSession.query.filter_by(org_id=org_id, session_id=session_id, revoked_at=None).first()
    if record:
        record.mark_seen()
        db.session.commit()


def make_session_identifier() -> str:
    return secrets.token_urlsafe(16)
