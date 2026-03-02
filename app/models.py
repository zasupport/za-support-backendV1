from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, JSON,
    Boolean, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


# --- Enums ---

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


# --- Models ---

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


class HealthData(Base):
    __tablename__ = "health_data"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_percent = Column(Float)
    battery_percent = Column(Float, nullable=True)
    threat_score = Column(Integer)
    raw_data = Column(JSON)


class NetworkData(Base):
    __tablename__ = "network_data"

    id = Column(Integer, primary_key=True, index=True)
    controller_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_clients = Column(Integer)
    total_devices = Column(Integer)
    raw_data = Column(JSON)


# --- Agent Device Management ---

class AgentDevice(Base):
    __tablename__ = "agent_devices"

    id = Column(Integer, primary_key=True, index=True)
    serial = Column(String, unique=True, index=True, nullable=False)
    model = Column(String, default="")
    hostname = Column(String, default="")
    os_version = Column(String, default="")
    agent_version = Column(String, default="")
    hardware_uuid = Column(String, default="")
    collection_interval = Column(Integer, default=300)
    heartbeat_interval = Column(Integer, default=60)
    command_poll_interval = Column(Integer, default=60)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    last_collection = Column(DateTime, nullable=True)

    collections = relationship("AgentCollection", back_populates="device", order_by="AgentCollection.received_at.desc()")
    commands = relationship("AgentCommand", back_populates="device", order_by="AgentCommand.created_at.desc()")


class AgentCollection(Base):
    __tablename__ = "agent_collections"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("agent_devices.id"), nullable=False)
    serial = Column(String, index=True, nullable=False)
    collection_type = Column(String, default="lite")
    received_at = Column(DateTime, default=datetime.utcnow)
    data = Column(JSON, nullable=False)
    alerts = Column(JSON, default=list)

    device = relationship("AgentDevice", back_populates="collections")


class AgentCommand(Base):
    __tablename__ = "agent_commands"

    id = Column(Integer, primary_key=True, index=True)
    command_id = Column(String, unique=True, index=True, nullable=False)
    device_id = Column(Integer, ForeignKey("agent_devices.id"), nullable=False)
    serial = Column(String, index=True, nullable=False)
    type = Column(String, nullable=False)
    payload = Column(String, default="")
    dispatched = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("AgentDevice", back_populates="commands")
    result = relationship("AgentCommandResult", back_populates="command", uselist=False)


class AgentCommandResult(Base):
    __tablename__ = "agent_command_results"

    id = Column(Integer, primary_key=True, index=True)
    command_id = Column(String, ForeignKey("agent_commands.command_id"), unique=True, index=True, nullable=False)
    serial = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False)
    result = Column(Text, default="")
    duration_seconds = Column(Integer, default=0)
    timestamp = Column(String, default="")
    received_at = Column(DateTime, default=datetime.utcnow)

    command = relationship("AgentCommand", back_populates="result")


class ISPAlert(Base):
    __tablename__ = "isp_alerts"

    id = Column(Integer, primary_key=True, index=True)
    isp_slug = Column(String, index=True, nullable=False)
    severity = Column(String, nullable=False)
    old_status = Column(String, nullable=False)
    new_status = Column(String, nullable=False)
    weighted_score = Column(Float, default=0)
    confirmed_down = Column(Integer, default=0)
    down_methods = Column(JSON, default=list)
    cycle = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
