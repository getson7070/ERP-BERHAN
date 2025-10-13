
from erp.extensions import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class ReorderPolicy(db.Model):
    __tablename__ = "reorder_policies"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = db.Column(UUID(as_uuid=True))
    warehouse_id = db.Column(UUID(as_uuid=True))
    service_level = db.Column(db.Numeric(4,2), default=0.95)
    safety_stock = db.Column(db.Numeric(18,3), default=0)
    reorder_point = db.Column(db.Numeric(18,3), default=0)
