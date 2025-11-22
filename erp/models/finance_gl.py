"""General ledger and reconciliation models with double-entry enforcement."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func

from erp.extensions import db


class GLJournalEntry(db.Model):
    """General ledger journal header with strong double-entry enforcement."""

    __tablename__ = "gl_journal_entries"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    journal_code = db.Column(db.String(32), nullable=False, default="GENERAL")
    reference = db.Column(db.String(64), nullable=True, index=True)
    description = db.Column(db.Text, nullable=True)

    currency = db.Column(db.String(8), nullable=False, default="ETB")
    fx_rate = db.Column(db.Numeric(14, 6), nullable=False, default=Decimal("1.000000"))
    base_currency = db.Column(db.String(8), nullable=True)

    document_date = db.Column(db.Date, nullable=False)
    posting_date = db.Column(db.Date, nullable=False)

    status = db.Column(db.String(16), nullable=False, default="draft", index=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    created_by_id = db.Column(db.Integer, nullable=True)
    posted_at = db.Column(db.DateTime, nullable=True)
    posted_by_id = db.Column(db.Integer, nullable=True)
    reversed_at = db.Column(db.DateTime, nullable=True)
    reversed_by_id = db.Column(db.Integer, nullable=True)

    lines = db.relationship(
        "GLJournalLine",
        back_populates="entry",
        cascade="all, delete-orphan",
        order_by="GLJournalLine.id",
    )

    def is_editable(self) -> bool:
        return self.status == "draft"

    def require_balanced(self) -> None:
        """Raise if debits != credits (in both tx and base currency)."""

        total_debit = Decimal("0")
        total_credit = Decimal("0")
        total_debit_base = Decimal("0")
        total_credit_base = Decimal("0")

        for line in self.lines:
            total_debit += line.debit or Decimal("0")
            total_credit += line.credit or Decimal("0")
            total_debit_base += line.debit_base or Decimal("0")
            total_credit_base += line.credit_base or Decimal("0")

        if total_debit != total_credit:
            raise ValueError(
                "Unbalanced in transaction currency: "
                f"debit={total_debit}, credit={total_credit}"
            )
        if total_debit_base != total_credit_base:
            raise ValueError(
                "Unbalanced in base currency: "
                f"debit_base={total_debit_base}, credit_base={total_credit_base}"
            )


class GLJournalLine(db.Model):
    """General ledger journal line."""

    __tablename__ = "gl_journal_lines"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    journal_entry_id = db.Column(
        db.Integer,
        db.ForeignKey("gl_journal_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    account_code = db.Column(db.String(64), nullable=False, index=True)
    account_name = db.Column(db.String(255), nullable=True)

    debit = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    credit = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0.00"))

    debit_base = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    credit_base = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0.00"))

    source_type = db.Column(db.String(32), nullable=True)
    source_id = db.Column(db.Integer, nullable=True)

    entry = db.relationship("GLJournalEntry", back_populates="lines")

    @property
    def net(self) -> Decimal:
        return (self.debit or Decimal("0")) - (self.credit or Decimal("0"))


class FinanceAuditLog(db.Model):
    """Immutable log for finance-sensitive actions."""

    __tablename__ = "finance_audit_log"

    id = db.Column(db.BigInteger, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    event_type = db.Column(db.String(64), nullable=False, index=True)
    entity_type = db.Column(db.String(64), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    payload = db.Column(db.JSON, nullable=False, default=dict)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    created_by_id = db.Column(db.Integer, nullable=True)


class BankStatement(db.Model):
    """Bank statement header used for reconciliation and audit."""

    __tablename__ = "bank_statements"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    bank_account_id = db.Column(
        db.Integer,
        db.ForeignKey("bank_accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    bank_account_code = db.Column(db.String(64), nullable=False, index=True)
    currency = db.Column(db.String(8), nullable=False, default="ETB")

    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)

    opening_balance = db.Column(db.Numeric(14, 2), nullable=False)
    closing_balance = db.Column(db.Numeric(14, 2), nullable=False)

    source = db.Column(db.String(64), nullable=True)
    external_reference = db.Column(db.String(128), nullable=True)

    # Legacy field retained for compatibility with previous banking UI
    statement_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    created_by_id = db.Column(db.Integer, nullable=True)

    lines = db.relationship(
        "BankStatementLine",
        back_populates="statement",
        cascade="all, delete-orphan",
        order_by="BankStatementLine.tx_date.asc()",
    )


class BankStatementLine(db.Model):
    __tablename__ = "bank_statement_lines"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    statement_id = db.Column(
        db.Integer,
        db.ForeignKey("bank_statements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tx_date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    balance = db.Column(db.Numeric(14, 2), nullable=True)

    # Compatibility fields for legacy banking upload screens
    reference = db.Column(db.String(64), nullable=True)
    posted_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    finance_entry_id = db.Column(db.Integer, nullable=True)

    matched = db.Column(db.Boolean, nullable=False, default=False, index=True)
    matched_journal_entry_id = db.Column(
        db.Integer,
        db.ForeignKey("gl_journal_entries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matched_at = db.Column(db.DateTime, nullable=True)
    matched_by_id = db.Column(db.Integer, nullable=True)

    statement = db.relationship("BankStatement", back_populates="lines")
    journal_entry = db.relationship("GLJournalEntry")


__all__ = [
    "GLJournalEntry",
    "GLJournalLine",
    "FinanceAuditLog",
    "BankStatement",
    "BankStatementLine",
]
