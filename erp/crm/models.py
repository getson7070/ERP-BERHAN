"""Backwards‑compatible CRM models.

from datetime import UTC, datetime
import uuid

from datetime import UTC, datetime
import uuid

from erp.extensions import db
from sqlalchemy.dialects.postgresql import UUID

class Lead(db.Model):
    __tablename__ = "crm_leads"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(32), default="New")  # New, Qualified, Disqualified, Converted
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

class Opportunity(db.Model):
    __tablename__ = "crm_opportunities"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(128), nullable=False)
    stage = db.Column(db.String(32), default="Prospecting")  # Prospecting, Proposal, Negotiation, Won, Lost
    value = db.Column(db.Numeric(18,2), default=0)

from __future__ import annotations

from erp.models import CrmLead as Lead, CrmInteraction as Interaction  # noqa: F401
from erp.models import SalesOpportunity  # noqa: F401

__all__ = ["Lead", "Interaction", "SalesOpportunity"]
