"""Client-facing authentication models: accounts, verification, resets, OAuth links."""
from __future__ import annotations

from datetime import datetime
import hashlib
import secrets
from uuid import uuid4

from flask_login import UserMixin

from erp.extensions import db


class ClientAccount(UserMixin, db.Model):
    """Login-capable account for external clients (separate from employees)."""

    __tablename__ = "client_accounts"

    # Internal integer PK (kept for backward compatibility).
    id = db.Column(db.Integer, primary_key=True)

    # Public, non-guessable identifier for external usage (bots, links, APIs).
    uuid = db.Column(
        db.String(36),
        nullable=False,
        unique=True,
        index=True,
        default=lambda: str(uuid4()),
    )

    org_id = db.Column(db.Integer, nullable=False, index=True)

    # Internal client key (can be used to link to other internal models).
    client_id = db.Column(db.Integer, nullable=False, index=True)

    # Optional strong linkage to Institution (supports hospitals, wholesalers,
    # retailers, distributors, etc.).
    institution_id = db.Column(
        db.Integer,
        db.ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    email = db.Column(db.String(255), nullable=True, index=True)
    phone = db.Column(db.String(32), nullable=True, index=True)

    password_hash = db.Column(db.String(255), nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    is_verified = db.Column(db.Boolean, nullable=False, default=False, index=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    verified_at = db.Column(db.DateTime, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)

    roles = db.relationship(
        "Role",
        secondary="client_role_assignments",
        backref="client_accounts",
        lazy="select",
    )

    __table_args__ = (
        db.UniqueConstraint("org_id", "email", name="uq_client_email"),
        db.UniqueConstraint("org_id", "phone", name="uq_client_phone"),
    )

    institution = db.relationship("Institution", backref="client_accounts")

    # ------------------------------------------------------------------
    # Flask-Login integration
    # ------------------------------------------------------------------
    def get_id(self) -> str:
        """
        Prefix ensures no collision with employee/internal users.

        Session IDs will look like: "client:123".
        """
        return f"client:{self.id}"

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    @property
    def public_id(self) -> str:
        """Stable, non-guessable identifier for use in URLs, APIs, bots."""
        return str(self.uuid)

    @property
    def is_fully_verified(self) -> bool:
        """
        Convenience flag: client account is active AND verified.
        """
        return bool(self.is_active and self.is_verified)


class ClientRoleAssignment(db.Model):
    """Associates client accounts with roles for RBAC checks."""

    __tablename__ = "client_role_assignments"
    __table_args__ = (
        db.UniqueConstraint("client_account_id", "role_id", name="uq_client_role"),
    )

    id = db.Column(db.Integer, primary_key=True)

    client_account_id = db.Column(
        db.Integer,
        db.ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())


class ClientVerification(db.Model):
    """OTP / identity verification codes for client activation."""

    __tablename__ = "client_verifications"

    id = db.Column(db.BigInteger, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    client_account_id = db.Column(
        db.Integer,
        db.ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    method = db.Column(db.String(16), nullable=False)  # sms, email
    code_hash = db.Column(db.String(128), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @staticmethod
    def make_code() -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    @staticmethod
    def hash_code(code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()


class ClientPasswordReset(db.Model):
    """One-time password reset tokens for client accounts."""

    __tablename__ = "client_password_resets"

    id = db.Column(db.BigInteger, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    client_account_id = db.Column(
        db.Integer,
        db.ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token_hash = db.Column(db.String(128), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    @staticmethod
    def make_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


class ClientOAuthAccount(db.Model):
    """Link OAuth identities (Google, Microsoft) to a client account."""

    __tablename__ = "client_oauth_accounts"
    __table_args__ = (
        db.UniqueConstraint(
            "org_id", "provider", "provider_user_id", name="uq_client_oauth"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    client_account_id = db.Column(
        db.Integer,
        db.ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider = db.Column(db.String(32), nullable=False, index=True)  # google, microsoft
    provider_user_id = db.Column(db.String(255), nullable=False, index=True)
    provider_email = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
