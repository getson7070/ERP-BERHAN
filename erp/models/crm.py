"""CRM domain models for accounts, contacts, pipeline events, tickets, and portal links."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from erp.extensions import db


class CRMAccount(db.Model):
    __tablename__ = "crm_accounts"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)

    code = db.Column(db.String(64), nullable=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    account_type = db.Column(db.String(32), nullable=False, default="customer")

    pipeline_stage = db.Column(db.String(32), nullable=False, default="lead", index=True)
    segment = db.Column(db.String(32), nullable=True, index=True)

    industry = db.Column(db.String(128), nullable=True)
    country = db.Column(db.String(64), nullable=True)
    city = db.Column(db.String(64), nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    credit_limit = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    payment_terms_days = db.Column(db.Integer, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    created_by_id = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    contacts = db.relationship(
        "CRMContact",
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="CRMContact.id",
    )
    pipeline_events = db.relationship(
        "CRMPipelineEvent",
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="CRMPipelineEvent.created_at.desc()",
    )
    tickets = db.relationship(
        "SupportTicket",
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="SupportTicket.created_at.desc()",
    )


class CRMContact(db.Model):
    __tablename__ = "crm_contacts"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)
    account_id = db.Column(
        db.Integer,
        db.ForeignKey("crm_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    full_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(128), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(64), nullable=True)

    is_primary = db.Column(db.Boolean, nullable=False, default=False)

    account = db.relationship("CRMAccount", back_populates="contacts")


class CRMPipelineEvent(db.Model):
    __tablename__ = "crm_pipeline_events"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)
    account_id = db.Column(
        db.Integer,
        db.ForeignKey("crm_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    from_stage = db.Column(db.String(32), nullable=False)
    to_stage = db.Column(db.String(32), nullable=False)
    reason = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    created_by_id = db.Column(db.Integer, nullable=True)

    account = db.relationship("CRMAccount", back_populates="pipeline_events")


class SupportTicket(db.Model):
    __tablename__ = "support_tickets"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)
    account_id = db.Column(
        db.Integer,
        db.ForeignKey("crm_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="open", index=True)
    priority = db.Column(db.String(32), nullable=False, default="normal")

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    created_by_id = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    account = db.relationship("CRMAccount", back_populates="tickets")


class ClientPortalLink(db.Model):
    """Links an internal user to a CRM account for the client portal."""

    __tablename__ = "client_portal_links"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True, unique=True)
    account_id = db.Column(
        db.Integer,
        db.ForeignKey("crm_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    account = db.relationship("CRMAccount")


__all__ = [
    "CRMAccount",
    "CRMContact",
    "CRMPipelineEvent",
    "SupportTicket",
    "ClientPortalLink",
]
