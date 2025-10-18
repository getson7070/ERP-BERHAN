from datetime import datetime
from erp.extensions import db

class ProductRecall(db.Model):
    __tablename__ = "product_recalls"
    id = db.Column(db.Integer, primary_key=True)
    ref = db.Column(db.String(64), unique=True, nullable=False, index=True)
    product_name = db.Column(db.String(255), nullable=False)
    lot = db.Column(db.String(128), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    risk_level = db.Column(db.String(16), nullable=False, default="medium")  # low/medium/high
    status = db.Column(db.String(16), nullable=False, default="open")  # open/closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    closed_at = db.Column(db.DateTime, nullable=True)
