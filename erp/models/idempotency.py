# erp/models/idempotency.py
from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy import Index, UniqueConstraint
from erp import db  # your SQLAlchemy db instance

class IdempotencyKey(db.Model):
    __tablename__ = "idempotency_keys"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), nullable=False)
    endpoint = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("key", name="uq_idem_key"),
        Index("ix_idem_endpoint", "endpoint"),
        Index("ix_idem_created_at", "created_at"),
    )

    @staticmethod
    def purge_older_than(hours: int = 24) -> int:
        """
        Delete old keys to keep the table small.
        Returns number of rows deleted.
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        res = db.session.query(IdempotencyKey).filter(IdempotencyKey.created_at < cutoff).delete()
        return res
