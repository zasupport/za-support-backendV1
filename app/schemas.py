from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, TicketStatus, TicketPriority, ChatSessionStatus, MessageType


# --- Auth ---

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: Optional[UserRole] = UserRole.customer


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Tickets ---

class TicketCreate(BaseModel):
    subject: str
    description: str
    priority: Optional[TicketPriority] = TicketPriority.medium


class TicketUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_agent_id: Optional[int] = None


class TicketOut(BaseModel):
    id: int
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    user_id: int
    assigned_agent_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Chat ---

class ChatSessionCreate(BaseModel):
    ticket_id: Optional[int] = None


class ChatSessionOut(BaseModel):
    id: int
    ticket_id: Optional[int]
    user_id: int
    agent_id: Optional[int]
    status: ChatSessionStatus
    created_at: datetime
    closed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    content: str
    message_type: Optional[MessageType] = MessageType.text


class ChatMessageOut(BaseModel):
    id: int
    session_id: int
    sender_id: int
    content: str
    message_type: MessageType
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Health ---

class HealthSubmission(BaseModel):
    machine_id: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    battery_percent: Optional[float] = None
    threat_score: int
    raw_data: dict


class HealthOut(BaseModel):
    id: int
    machine_id: str
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    battery_percent: Optional[float]
    threat_score: int

    model_config = {"from_attributes": True}


# --- Network ---

class NetworkSubmission(BaseModel):
    controller_id: str
    total_clients: int
    total_devices: int
    raw_data: dict


class NetworkOut(BaseModel):
    id: int
    controller_id: str
    timestamp: datetime
    total_clients: int
    total_devices: int

    model_config = {"from_attributes": True}
