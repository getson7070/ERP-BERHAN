from __future__ import annotations

from datetime import datetime

import pyotp

from erp.extensions import db
from erp.models import UserMFA, UserMFABackupCode


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_totp_uri(user_email: str, secret: str, issuer: str = "ERP-BERHAN") -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=user_email, issuer_name=issuer)


def verify_totp(secret: str | None, code: str) -> bool:
    if not secret:
        return False
    totp = pyotp.TOTP(secret)
    return bool(totp.verify(code, valid_window=1))


def enable_mfa(org_id: int, user_id: int, secret: str) -> UserMFA:
    mfa = UserMFA.query.filter_by(org_id=org_id, user_id=user_id).first()
    if mfa is None:
        mfa = UserMFA(org_id=org_id, user_id=user_id)
        db.session.add(mfa)

    mfa.totp_secret = secret
    mfa.is_enabled = True
    mfa.enrolled_at = datetime.utcnow()
    db.session.commit()
    return mfa


def disable_mfa(org_id: int, user_id: int) -> None:
    mfa = UserMFA.query.filter_by(org_id=org_id, user_id=user_id).first()
    if mfa:
        mfa.is_enabled = False
        mfa.totp_secret = None
        db.session.commit()


def generate_backup_codes(org_id: int, user_id: int, count: int = 8) -> list[str]:
    UserMFABackupCode.query.filter_by(org_id=org_id, user_id=user_id, used_at=None).delete()
    codes: list[str] = []
    for _ in range(count):
        raw = UserMFABackupCode.make_code()
        codes.append(raw)
        db.session.add(
            UserMFABackupCode(
                org_id=org_id,
                user_id=user_id,
                code_hash=UserMFABackupCode.hash_code(raw),
            )
        )
    db.session.commit()
    return codes


def verify_backup_code(org_id: int, user_id: int, code: str) -> bool:
    hashed = UserMFABackupCode.hash_code(code)
    record = UserMFABackupCode.query.filter_by(
        org_id=org_id, user_id=user_id, code_hash=hashed, used_at=None
    ).first()
    if not record:
        return False
    record.used_at = datetime.utcnow()
    db.session.commit()
    return True
