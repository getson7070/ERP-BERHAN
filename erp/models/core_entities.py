"""Core cross-domain models that connect ERP modules together.

The previous codebase relied on placeholders without persistent state,
which prevented modules such as analytics, approvals, CRM, finance,
and maintenance from interacting.  These SQLAlchemy models define the
shared entities required by the upgraded blueprints.
"""
from __future__ import annotations

from datetime import UTC, datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, Enum, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db


class TimestampMixin:
    """Reusable columns for creation and update tracking."""

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class OrgScopedMixin:
    """Mixin that associates rows with an organisation/tenant."""

    org_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )


class AnalyticsEvent(TimestampMixin, OrgScopedMixin, db.Model):
    """Persisted frontend vitals or KPI snapshots collected by analytics."""

    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    metric: Mapped[str] = mapped_column(db.String(64), nullable=False, index=True)
    value: Mapped[float] = mapped_column(db.Float, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False, index=True
    )


class ApprovalRequest(TimestampMixin, OrgScopedMixin, db.Model):
    """Workflow approval requests referencing orders or other documents."""

    __tablename__ = "approval_requests"
    __table_args__ = (
        Index("ix_approval_requests_order", "order_id"),
        Index("ix_approval_requests_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        db.String(32), nullable=False, default="pending"
    )  # pending|approved|rejected
    requested_by: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_by: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(db.Text)

    order = relationship("Order", backref="approval_requests")


class MaintenanceTicket(TimestampMixin, OrgScopedMixin, db.Model):
    """Maintenance request raised by users and fulfilled by operations."""

    __tablename__ = "maintenance_tickets"
    __table_args__ = (
        Index("ix_maintenance_status", "status"),
        Index("ix_maintenance_asset", "asset_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_name: Mapped[str] = mapped_column(db.String(128), nullable=False)
    description: Mapped[str] = mapped_column(db.Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        db.String(16), nullable=False, default="medium"
    )  # low|medium|high
    status: Mapped[str] = mapped_column(
        db.String(16), nullable=False, default="open"
    )  # open|in_progress|closed
    order_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    assigned_to: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    due_date: Mapped[Optional[date]] = mapped_column(db.Date)
    closed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime)

    order = relationship("Order", backref="maintenance_tickets")


class CrmLead(TimestampMixin, OrgScopedMixin, db.Model):
    """Customer relationship management lead."""

    __tablename__ = "crm_leads"
    __table_args__ = (Index("ix_crm_leads_status", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(db.String(255), index=True)
    phone: Mapped[Optional[str]] = mapped_column(db.String(50))
    status: Mapped[str] = mapped_column(
        db.String(32), nullable=False, default="new"
    )  # new|contacted|qualified|won|lost
    potential_value: Mapped[Optional[Decimal]] = mapped_column(
        db.Numeric(14, 2), nullable=True
    )
    order_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )

    interactions = relationship(
        "CrmInteraction", back_populates="lead", cascade="all, delete-orphan"
    )


class CrmInteraction(TimestampMixin, db.Model):
    """Logged activity or notes against a CRM lead."""

    __tablename__ = "crm_interactions"
    __table_args__ = (Index("ix_crm_interactions_lead", "lead_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("crm_leads.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str] = mapped_column(db.Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False
    )

    lead = relationship("CrmLead", back_populates="interactions")


class FinanceAccount(TimestampMixin, OrgScopedMixin, db.Model):
    """General ledger account."""

    __tablename__ = "finance_accounts"
    __table_args__ = (
        UniqueConstraint("org_id", "code", name="uq_finance_accounts_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(db.String(32), nullable=False)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        Enum(
            "asset",
            "liability",
            "equity",
            "income",
            "expense",
            name="finance_account_category",
        ),
        nullable=False,
        default="asset",
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class FinanceEntry(TimestampMixin, OrgScopedMixin, db.Model):
    """Journal entry lines for ledger accounting."""

    __tablename__ = "finance_entries"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_finance_entries_amount_positive"),
        Index("ix_finance_entries_account", "account_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("finance_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    bank_transaction_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("bank_transactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(db.Numeric(14, 2), nullable=False)
    direction: Mapped[str] = mapped_column(
        Enum("debit", "credit", name="finance_entry_direction"),
        nullable=False,
    )
    memo: Mapped[Optional[str]] = mapped_column(db.String(255))
    posted_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, nullable=False, index=True
    )

    account = relationship("FinanceAccount", backref="entries")


class BankTransaction(TimestampMixin, OrgScopedMixin, db.Model):
    """Transactions recorded against a bank account."""

    __tablename__ = "bank_transactions"
    __table_args__ = (Index("ix_bank_transactions_account", "bank_account_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    bank_account_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("bank_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    direction: Mapped[str] = mapped_column(
        Enum("inflow", "outflow", name="bank_transaction_direction"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(db.Numeric(14, 2), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(db.String(255))
    posted_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False
    )


class SupplyChainShipment(TimestampMixin, OrgScopedMixin, db.Model):
    """Shipments tied to supply chain fulfilment."""

    __tablename__ = "supply_chain_shipments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    vendor_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        db.String(32), nullable=False, default="expected"
    )  # expected|in_transit|received|delayed
    expected_date: Mapped[Optional[date]] = mapped_column(db.Date)
    shipped_date: Mapped[Optional[date]] = mapped_column(db.Date)
    received_date: Mapped[Optional[date]] = mapped_column(db.Date)


class InventoryReservation(TimestampMixin, OrgScopedMixin, db.Model):
    """Links orders to reserved inventory quantities."""

    __tablename__ = "inventory_reservations"
    __table_args__ = (
        UniqueConstraint(
            "order_id", "inventory_item_id", name="uq_inventory_reservations_unique"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    inventory_item_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(db.Integer, nullable=False)


class ClientRegistration(TimestampMixin, OrgScopedMixin, db.Model):
    """Pending client onboarding requests surfaced in user management."""

    __tablename__ = "client_registrations"
    __table_args__ = (
        Index("ix_client_registrations_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        db.String(16), nullable=False, default="pending"
    )  # pending|approved|rejected
    decided_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True))


class UserRoleAssignment(TimestampMixin, db.Model):
    """Associates users with roles for access control."""

    __tablename__ = "user_role_assignments"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role_assignments"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )


class SalesOpportunity(TimestampMixin, OrgScopedMixin, db.Model):
    """Sales pipeline opportunity linked to CRM leads and orders."""

    __tablename__ = "sales_opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(db.Numeric(14, 2), nullable=False)
    probability: Mapped[float] = mapped_column(
        db.Float, nullable=False, default=0.5
    )  # 0..1
    stage: Mapped[str] = mapped_column(
        Enum("prospecting", "proposal", "negotiation", "won", "lost", name="sales_opportunity_stage"),
        nullable=False,
        default="prospecting",
    )
    lead_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("crm_leads.id", ondelete="SET NULL"), nullable=True
    )
    order_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )


__all__ = [
    "AnalyticsEvent",
    "ApprovalRequest",
    "MaintenanceTicket",
    "CrmLead",
    "CrmInteraction",
    "FinanceAccount",
    "FinanceEntry",
    "BankTransaction",
    "SupplyChainShipment",
    "InventoryReservation",
    "ClientRegistration",
    "UserRoleAssignment",
    "SalesOpportunity",
]
