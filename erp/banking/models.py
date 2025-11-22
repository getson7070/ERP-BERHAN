"""Banking models – fully fixed for double-import issue and syntax errors."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from erp.extensions import db

# Prevent circular imports at runtime
if TYPE_CHECKING:
    from erp.models.finance_gl import BankStatement, BankStatementLine


class BankAccount(db.Model):
    __tablename__ = "bank_accounts"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(db.String(128), nullable=False)
    bank_name: Mapped[str] = mapped_column(db.String(255), nullable=False, default="")
    currency: Mapped[str] = mapped_column(db.String(8), nullable=False, default="ETB")
    account_number: Mapped[str | None] = mapped_column(db.String(64), nullable=True, unique=True)
    account_number_masked: Mapped[str] = mapped_column(db.String(64), nullable=False, default="")
    gl_account_code: Mapped[str] = mapped_column(db.String(64), nullable=False, default="", index=True)
    is_default: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)
    initial_balance: Mapped[Decimal] = mapped_column(
        db.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, nullable=False, server_default=func.now()
    )
    created_by_id: Mapped[int | None] = mapped_column(db.Integer, nullable=True)

    statements = relationship(
        "BankStatement", back_populates="bank_account", cascade="all, delete-orphan"
    )
    transactions = relationship(
        "BankTransaction", backref="bank_account", cascade="all, delete-orphan"
    )

    # Indexes & constraints
    Index("ix_bank_accounts_org", "org_id")
    CheckConstraint("initial_balance >= 0", name="ck_bank_accounts_balance_positive")



class BankConnection(db.Model):
    __tablename__ = "bank_connections"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(db.Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    provider: Mapped[str] = mapped_column(db.String(64), nullable=False)
    environment: Mapped[str] = mapped_column(db.String(32), nullable=False, default="sandbox")
    api_base_url: Mapped[str | None] = mapped_column(db.String(255))
    credentials_json = mapped_column(db.JSON, nullable=True, default=dict)
    requires_two_factor: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    two_factor_method: Mapped[str | None] = mapped_column(db.String(32))
    last_connected_at: Mapped[datetime | None] = mapped_column(db.DateTime)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, server_default=func.now())
    created_by_id: Mapped[int | None] = mapped_column(db.Integer)


class BankAccessToken(db.Model):
    __tablename__ = "bank_access_tokens"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(db.Integer, nullable=False, index=True)
    connection_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("bank_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    access_token: Mapped[str] = mapped_column(db.String(4096), nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(db.String(4096))
    token_type: Mapped[str | None] = mapped_column(db.String(64))
    scope: Mapped[str | None] = mapped_column(db.String(512))
    expires_at: Mapped[datetime | None] = mapped_column(db.DateTime)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, server_default=func.now())
    created_by_id: Mapped[int | None] = mapped_column(db.Integer)

    connection = relationship("BankConnection", backref="tokens")


class BankTwoFactorChallenge(db.Model):
    __tablename__ = "bank_two_factor_challenges"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(db.Integer, nullable=False, index=True)
    connection_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("bank_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    challenge_type: Mapped[str] = mapped_column(db.String(32), nullable=False)
    challenge_id: Mapped[str | None] = mapped_column(db.String(128))
    status: Mapped[str] = mapped_column(db.String(32), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, server_default=func.now())
    created_by_id: Mapped[int | None] = mapped_column(db.Integer)
    resolved_at: Mapped[datetime | None] = mapped_column(db.DateTime)
    resolved_by_id: Mapped[int | None] = mapped_column(db.Integer)


class BankSyncJob(db.Model):
    __tablename__ = "bank_sync_jobs"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(db.Integer, nullable=False, index=True)
    connection_id: Mapped[int | None] = mapped_column(
        db.Integer, db.ForeignKey("bank_connections.id", ondelete="SET NULL"), nullable=True, index=True
    )
    bank_account_id: Mapped[int | None] = mapped_column(
        db.Integer  , db.ForeignKey("bank_accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(db.String(32), nullable=False, default="pending", index=True)
    requested_from: Mapped[datetime | None] = mapped_column(db.Date)
    requested_to: Mapped[datetime | None] = mapped_column(db.Date)
    started_at: Mapped[datetime | None] = mapped_column(db.DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(db.DateTime)
    requested_by_id: Mapped[int | None] = mapped_column(db.Integer)
    statements_created: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    lines_created: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(db.Text)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, server_default=func.now())

    connection = relationship("BankConnection")
    bank_account = relationship("BankAccount")


# Safe back-populates after all classes are defined
from erp.models.finance_gl import BankStatement, BankStatementLine

BankStatement.bank_account = relationship(
    "BankAccount",
    primaryjoin="BankStatement.bank_account_id == BankAccount.id",
    back_populates="statements",
)

StatementLine = BankStatementLine

__all__ = [
    "BankAccount",    "BankConnection",
    "BankAccessToken",
    "BankTwoFactorChallenge",
    "BankSyncJob",
    "BankStatement",
    "BankStatementLine",
    "StatementLine",
]