import enum
from datetime import datetime

from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from app.core.database import Base


class ChatSessionStatus(str, enum.Enum):
    active = "active"
    closed = "closed"


class MessageType(str, enum.Enum):
    text = "text"
    system = "system"
    file = "file"


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
