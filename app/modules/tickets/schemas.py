from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.modules.tickets.models import TicketStatus, TicketPriority


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
