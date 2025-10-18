# erp/models/user.py
from datetime import datetime
from erp.extensions import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # add other fields you need...

class DeviceAuthorization(db.Model):
    __tablename__ = "device_authorizations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_fingerprint = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("device_authorizations", lazy="dynamic"))

class ElectronicSignature(db.Model):
    __tablename__ = "electronic_signatures"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    intent = db.Column(db.String(255), nullable=False)
    signed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    prev_hash = db.Column(db.String(255))
    signature_hash = db.Column(db.String(255), nullable=False)

class DataLineage(db.Model):
    __tablename__ = "data_lineage"

    id = db.Column(db.Integer, primary_key=True)
    source_table = db.Column(db.String(255), nullable=False)
    target_table = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
