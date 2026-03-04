from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.modules.chat.models import ChatSessionStatus, MessageType


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
