# erp/models/user_dashboard.py
from erp.extensions import db

class UserDashboard(db.Model):
    __tablename__ = "user_dashboards"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)
    layout = db.Column(db.JSON, nullable=False, default=dict)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    user = db.relationship("User", backref=db.backref("dashboard", uselist=False))
