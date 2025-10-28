"""Module: models/trusted_device.py — audit-added docstring. Refine with precise purpose when convenient."""
# erp/models/trusted_device.py
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base  # assumes you have a Base (declarative) alongside your other models

class TrustedDevice(Base):
    __tablename__ = "trusted_devices"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    fingerprint = Column(String(128), nullable=False)  # store hashed fingerprint
    device_label = Column(String(100), nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=365), nullable=False)
    approved = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="trusted_devices")

    __table_args__ = (
        UniqueConstraint("fingerprint", name="uq_trusted_devices_fingerprint"),
    )

