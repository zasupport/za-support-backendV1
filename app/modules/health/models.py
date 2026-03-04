from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class HealthData(Base):
    __tablename__ = "health_data"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(128), ForeignKey("devices.machine_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_percent = Column(Float)
    battery_percent = Column(Float, nullable=True)
    battery_cycle_count = Column(Integer, nullable=True)
    battery_health = Column(String(32), nullable=True)
    threat_score = Column(Integer, default=0)
    uptime_hours = Column(Float, nullable=True)
    network_up_mbps = Column(Float, nullable=True)
    network_down_mbps = Column(Float, nullable=True)
    encrypted_raw = Column(Text, nullable=True)
    raw_data = Column(JSON, nullable=True)

    device = relationship("Device", back_populates="health_records")

    __table_args__ = (
        Index("ix_health_machine_ts", "machine_id", "timestamp"),
    )
