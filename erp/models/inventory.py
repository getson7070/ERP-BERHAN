from __future__ import annotations
from flask_sqlalchemy import SQLAlchemy
from erp import db

db = db  # reuse the same db instance from erp package

class Inventory(db.Model):
    __tablename__ = "inventory"
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, index=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    sku = db.Column(db.String(64), unique=True, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Numeric(12,2))

    @classmethod
    def tenant_query(cls, org_id):
        return cls.query.filter_by(org_id=org_id)
