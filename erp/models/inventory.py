from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Column

db = SQLAlchemy()

class Inventory(db.Model):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, nullable=False)           # NEW
    name = Column(String, nullable=False)
    sku = Column(String, unique=False, nullable=False) # uniqueness may be per-org in tests
    quantity = Column(Integer, default=0)
