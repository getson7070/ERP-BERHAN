
from erp.extensions import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class Lead(db.Model):
    __tablename__ = "crm_leads"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(32), default="New")  # New, Qualified, Disqualified, Converted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Opportunity(db.Model):
    __tablename__ = "crm_opportunities"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(128), nullable=False)
    stage = db.Column(db.String(32), default="Prospecting")  # Prospecting, Proposal, Negotiation, Won, Lost
    value = db.Column(db.Numeric(18,2), default=0)


