"""Banking models implemented with portable SQLAlchemy columns.

The previous implementation relied on PostgreSQL-specific UUID types.
To support SQLite (used in local development and tests) we switch to
integer identifiers while keeping business semantics intact.
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from erp.models import db
from erp.models.finance_gl import BankStatement, BankStatementLine


class BankAccount(db.Model):
    """Bank account configured for an organisation."""

    __tablename__ = "bank_accounts"
    __table_args__ = (
        Index("ix_bank_accounts_org", "org_id"),
        CheckConstraint("initial_balance >= 0", name="ck_bank_accounts_balance_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(db.String(128), nullable=False)
    currency: Mapped[str] = mapped_column(db.String(8), nullable=False, default="ETB")
    account_number: Mapped[str] = mapped_column(db.String(64), nullable=True, unique=True)
    initial_balance: Mapped[Decimal] = mapped_column(
        db.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )

    statements = relationship(
        "BankStatement", back_populates="bank_account", cascade="all, delete-orphan"
    )
    transactions = relationship(
        "BankTransaction", backref="bank_account", cascade="all, delete-orphan"
    )


class BankTransaction(db.Model):
    """Simple transaction log for inflows/outflows."""

    __tablename__ = "bank_transactions"
    __table_args__ = (Index("ix_bank_transactions_org", "org_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(db.Integer, nullable=False)
    bank_account_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False
    )
    direction: Mapped[str] = mapped_column(db.String(16), nullable=False)
    amount: Mapped[Decimal] = mapped_column(db.Numeric(14, 2), nullable=False)
    reference: Mapped[str | None] = mapped_column(db.String(128))
    posted_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)


# Back-populate relationship now that BankStatement is imported
BankStatement.bank_account = relationship(
    "BankAccount",
    primaryjoin="BankStatement.bank_account_id==BankAccount.id",
    back_populates="statements",
)


StatementLine = BankStatementLine

__all__ = [
    "BankAccount",
    "BankStatement",
    "BankStatementLine",
    "StatementLine",
    "BankTransaction",
]
