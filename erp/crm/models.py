"""Backwards-compatible CRM models with unified exports."""

from __future__ import annotations

import uuid

from sqlalchemy.dialects.postgresql import UUID

from erp.extensions import db
from erp.models import (
    CRMAccount,
    CRMContact,
    CRMPipelineEvent,
    SupportTicket,
    ClientPortalLink,
    CrmLead as Lead,
    CrmInteraction as Interaction,
    SalesOpportunity,
)


class Opportunity(db.Model):
    __tablename__ = "crm_opportunities"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(128), nullable=False)
    stage = db.Column(db.String(32), default="Prospecting")  # Prospecting, Proposal, Negotiation, Won, Lost
    value = db.Column(db.Numeric(18, 2), default=0)


__all__ = [
    "Lead",
    "Interaction",
    "SalesOpportunity",
    "Opportunity",
    "CRMAccount",
    "CRMContact",
    "CRMPipelineEvent",
    "SupportTicket",
    "ClientPortalLink",
]
