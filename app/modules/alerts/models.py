import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    WARNING = "warning"
    INFO = "info"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(128), ForeignKey("devices.machine_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    severity = Column(String(16), default=AlertSeverity.INFO.value)
    category = Column(String(64), nullable=False)
    message = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    device = relationship("Device", back_populates="alerts")

    __table_args__ = (
        Index("ix_alert_machine_sev", "machine_id", "severity"),
    )
