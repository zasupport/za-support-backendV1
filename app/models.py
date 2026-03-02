from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, JSON,
    Boolean, ForeignKey, Index, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


# --- Enums (V1 original) ---

class UserRole(str, enum.Enum):
    customer = "customer"
    agent = "agent"
    admin = "admin"


class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class TicketPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ChatSessionStatus(str, enum.Enum):
    active = "active"
    closed = "closed"


class MessageType(str, enum.Enum):
    text = "text"
    system = "system"
    file = "file"


# --- Enums (ported from old repo) ---

class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    WARNING = "warning"
    INFO = "info"


class DeviceType(str, enum.Enum):
    MAC_DESKTOP = "mac_desktop"
    MAC_LAPTOP = "mac_laptop"
    IPHONE = "iphone"
    IPAD = "ipad"
    OTHER = "other"


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


# --- Models (V1 original) ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.customer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tickets = relationship("Ticket", back_populates="user", foreign_keys="Ticket.user_id")
    assigned_tickets = relationship("Ticket", back_populates="assigned_agent", foreign_keys="Ticket.assigned_agent_id")
    chat_messages = relationship("ChatMessage", back_populates="sender")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SAEnum(TicketStatus), default=TicketStatus.open, nullable=False)
    priority = Column(SAEnum(TicketPriority), default=TicketPriority.medium, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="tickets", foreign_keys=[user_id])
    assigned_agent = relationship("User", back_populates="assigned_tickets", foreign_keys=[assigned_agent_id])
    chat_sessions = relationship("ChatSession", back_populates="ticket")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(SAEnum(ChatSessionStatus), default=ChatSessionStatus.active, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    ticket = relationship("Ticket", back_populates="chat_sessions")
    user = relationship("User", foreign_keys=[user_id])
    agent = relationship("User", foreign_keys=[agent_id])
    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(SAEnum(MessageType), default=MessageType.text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
    sender = relationship("User", back_populates="chat_messages")


# --- Device Registry (ported from old repo) ---

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


# --- Health Telemetry (enhanced with old repo fields) ---

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


# --- Network Telemetry (enhanced with old repo fields) ---

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


# --- Alerts (ported from old repo) ---

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


# --- Workshop Diagnostics (ported from old repo) ---

class WorkshopDiagnostic(Base):
    __tablename__ = "workshop_diagnostics"

    id = Column(Integer, primary_key=True, index=True)

    # Identity
    serial_number = Column(String(64), nullable=False, index=True)
    hostname = Column(String(256), nullable=True)
    client_id = Column(String(128), nullable=True, index=True)
    diagnostic_version = Column(String(16), nullable=True)
    mode = Column(String(16), nullable=True)

    # Hardware summary
    chip_type = Column(String(32), nullable=True)
    model_name = Column(String(128), nullable=True)
    model_identifier = Column(String(64), nullable=True)
    ram_gb = Column(Integer, nullable=True)
    ram_upgradeable = Column(String(128), nullable=True)
    cpu_name = Column(String(128), nullable=True)
    cores_physical = Column(Integer, nullable=True)
    cores_logical = Column(Integer, nullable=True)

    # macOS
    macos_version = Column(String(32), nullable=True)
    macos_build = Column(String(32), nullable=True)
    uptime_seconds = Column(Integer, nullable=True)

    # Security
    sip_enabled = Column(Boolean, nullable=True)
    filevault_on = Column(Boolean, nullable=True)
    firewall_on = Column(Boolean, nullable=True)
    gatekeeper_on = Column(Boolean, nullable=True)
    xprotect_version = Column(String(32), nullable=True)
    password_manager = Column(String(64), nullable=True)
    av_edr = Column(String(128), nullable=True)

    # Battery
    battery_health_pct = Column(Float, nullable=True)
    battery_cycles = Column(Integer, nullable=True)
    battery_design_capacity = Column(Integer, nullable=True)
    battery_max_capacity = Column(Integer, nullable=True)
    battery_condition = Column(String(32), nullable=True)

    # Storage
    disk_used_pct = Column(Integer, nullable=True)
    disk_free_gb = Column(Integer, nullable=True)

    # OCLP
    oclp_detected = Column(Boolean, default=False)
    oclp_version = Column(String(32), nullable=True)
    oclp_root_patched = Column(Boolean, default=False)
    third_party_kexts = Column(Integer, default=0)

    # Diagnostics summary
    kernel_panics = Column(Integer, default=0)
    total_processes = Column(Integer, nullable=True)

    # Intelligence engine output
    recommendations = Column(JSON, nullable=True)
    recommendation_count = Column(Integer, default=0)

    # Full payload
    raw_json = Column(JSON, nullable=True)
    runtime_seconds = Column(Integer, nullable=True)

    # Timestamps
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_diag_serial_captured", "serial_number", "captured_at"),
        Index("ix_diag_client_captured", "client_id", "captured_at"),
    )


# --- ISP Outage Monitor (ported from old repo) ---

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
