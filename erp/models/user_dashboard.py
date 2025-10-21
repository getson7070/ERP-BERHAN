from __future__ import annotations
from datetime import datetime
from erp.models import db

class UserDashboard(db.Model):
    __tablename__ = "user_dashboards"
    __table_args__ = (db.UniqueConstraint("user_id", name="uq_user_dashboard_user"),)

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # keep it simple: store JSON as text; app/tests can dump()/load() as needed
    layout  = db.Column(db.Text, nullable=True)          # JSON string of widget layout
    theme   = db.Column(db.String(32), nullable=True, default="light")
    widgets = db.Column(db.Text, nullable=True)          # optional JSON string of widgets

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship(
        "User",
        backref=db.backref("dashboard", uselist=False, cascade="all, delete-orphan", lazy=True),
        foreign_keys=[user_id],
    )

    @classmethod
    def get_or_create(cls, user_id: int) -> "UserDashboard":
        obj = cls.query.filter_by(user_id=user_id).first()
        if not obj:
            obj = cls(user_id=user_id)
            db.session.add(obj)
        return obj

    def set_layout(self, layout_json: str) -> None:
        self.layout = layout_json
        self.updated_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<UserDashboard id={self.id} user_id={self.user_id}>"



