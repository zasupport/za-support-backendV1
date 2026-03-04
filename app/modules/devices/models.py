import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class DeviceType(str, enum.Enum):
    MAC_DESKTOP = "mac_desktop"
    MAC_LAPTOP = "mac_laptop"
    IPHONE = "iphone"
    IPAD = "ipad"
    OTHER = "other"


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(128), unique=True, nullable=False, index=True)
    client_id = Column(String(128), nullable=True, index=True)
    hostname = Column(String(256), nullable=True)
    device_type = Column(String(32), default=DeviceType.OTHER.value)
    model_identifier = Column(String(128), nullable=True)
    serial_number = Column(String(64), nullable=True, index=True)
    os_version = Column(String(64), nullable=True)
    agent_version = Column(String(32), nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    registered_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    health_records = relationship("HealthData", back_populates="device", lazy="dynamic")
    alerts = relationship("Alert", back_populates="device", lazy="dynamic")
