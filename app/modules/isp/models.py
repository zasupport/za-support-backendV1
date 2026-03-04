import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class ISPStatus(str, enum.Enum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    OUTAGE = "outage"
    UNKNOWN = "unknown"


class CheckSource(str, enum.Enum):
    STATUS_PAGE = "status_page"
    DOWNDETECTOR = "downdetector"
    HTTP_PROBE = "http_probe"
    AGENT_CONNECTIVITY = "agent_connectivity"


class ConnectivityState(str, enum.Enum):
    CONNECTED = "connected"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"
    UNKNOWN = "unknown"


class ISPProvider(Base):
    __tablename__ = "isp_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    status_page_url = Column(String(512), nullable=True)
    downdetector_slug = Column(String(128), nullable=True)
    probe_targets = Column(JSON, nullable=True)
    gateway_ip = Column(String(45), nullable=True)
    underlying_provider = Column(String(128), nullable=True)
    current_status = Column(String(16), default=ISPStatus.OPERATIONAL.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    status_checks = relationship("ISPStatusCheck", back_populates="provider", lazy="dynamic")
    connectivity_records = relationship("AgentConnectivity", back_populates="provider", lazy="dynamic")
    outages = relationship("ISPOutage", back_populates="provider", lazy="dynamic")


class ISPStatusCheck(Base):
    __tablename__ = "isp_status_checks"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("isp_providers.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String(32), nullable=False)
    status = Column(String(16), default=ISPStatus.OPERATIONAL.value)
    response_time_ms = Column(Float, nullable=True)
    http_status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    is_healthy = Column(Boolean, default=True)

    provider = relationship("ISPProvider", back_populates="status_checks")

    __table_args__ = (
        Index("ix_isp_check_provider_ts", "provider_id", "timestamp"),
        Index("ix_isp_check_source_ts", "source", "timestamp"),
    )


class AgentConnectivity(Base):
    __tablename__ = "agent_connectivity"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(128), ForeignKey("devices.machine_id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("isp_providers.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    state = Column(String(16), default=ConnectivityState.CONNECTED.value)
    latency_ms = Column(Float, nullable=True)
    packet_loss_pct = Column(Float, nullable=True)
    gateway_reachable = Column(Boolean, nullable=True)
    dns_reachable = Column(Boolean, nullable=True)

    provider = relationship("ISPProvider", back_populates="connectivity_records")

    __table_args__ = (
        Index("ix_agent_conn_machine_ts", "machine_id", "timestamp"),
        Index("ix_agent_conn_provider_ts", "provider_id", "timestamp"),
    )


class ISPOutage(Base):
    __tablename__ = "isp_outages"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("isp_providers.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    ended_at = Column(DateTime, nullable=True)
    severity = Column(String(16), default=ISPStatus.OUTAGE.value)
    confirmed = Column(Boolean, default=False)
    confirmation_sources = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    auto_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    provider = relationship("ISPProvider", back_populates="outages")
