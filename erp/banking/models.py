"""Banking models implemented with portable SQLAlchemy columns.

The previous implementation relied on PostgreSQL-specific UUID types.
To support SQLite (used in local development and tests) we switch to
integer identifiers while keeping business semantics intact.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from erp.models import db


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


class BankStatement(db.Model):
    """Monthly or ad-hoc statement summarising account activity."""

    __tablename__ = "bank_statements"
    __table_args__ = (
        Index("ix_bank_statements_account", "bank_account_id"),
        Index("ix_bank_statements_period", "statement_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    bank_account_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("bank_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    statement_date: Mapped[date] = mapped_column(default=date.today, nullable=False)
    closing_balance: Mapped[Decimal] = mapped_column(
        db.Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )

    bank_account = relationship("BankAccount", back_populates="statements")
    lines = relationship(
        "StatementLine", back_populates="statement", cascade="all, delete-orphan"
    )


class StatementLine(db.Model):
    """Individual debit/credit entries on a statement."""

    __tablename__ = "bank_statement_lines"
    __table_args__ = (Index("ix_statement_lines_statement", "statement_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    statement_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("bank_statements.id", ondelete="CASCADE"),
        nullable=False,
    )
    posted_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(
        db.Numeric(14, 2), nullable=False
    )
    description: Mapped[str | None] = mapped_column(db.String(255))
    reference: Mapped[str | None] = mapped_column(db.String(64))
    finance_entry_id: Mapped[int | None] = mapped_column(
        db.Integer, db.ForeignKey("finance_entries.id", ondelete="SET NULL"), nullable=True
    )

    statement = relationship("BankStatement", back_populates="lines")


__all__ = ["BankAccount", "BankStatement", "StatementLine"]
