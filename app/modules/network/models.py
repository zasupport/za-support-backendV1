from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Index

from app.core.database import Base


class NetworkData(Base):
    __tablename__ = "network_data"

    id = Column(Integer, primary_key=True, index=True)
    controller_id = Column(String(128), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    total_clients = Column(Integer)
    total_devices = Column(Integer)
    wan_status = Column(String(16), nullable=True)
    wan_latency_ms = Column(Float, nullable=True)
    raw_data = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_network_controller_ts", "controller_id", "timestamp"),
    )
