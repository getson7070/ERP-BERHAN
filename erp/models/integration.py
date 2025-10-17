from datetime import datetime
from erp.extensions import db

class IntegrationConfig(db.Model):
    __tablename__ = "integration_configs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    provider = db.Column(db.String(64), nullable=False)  # e.g., 'slack', 'telegram', 'webhook'
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    config_json = db.Column(db.JSON, default=dict, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
