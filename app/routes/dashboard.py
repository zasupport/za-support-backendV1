from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, Ticket, ChatSession, ChatMessage, HealthData, NetworkData, Device, Alert, ISPProvider, ISPOutage
from app.models import TicketStatus, UserRole, ChatSessionStatus
from app.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregated dashboard statistics for agents and admins."""
    if current_user.role == UserRole.customer:
        # Customers get their own stats
        return _customer_stats(db, current_user.id)
    return _admin_stats(db)


def _customer_stats(db: Session, user_id: int) -> dict:
    my_tickets = db.query(Ticket).filter(Ticket.user_id == user_id)
    my_sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id)

    return {
        "my_tickets": {
            "total": my_tickets.count(),
            "open": my_tickets.filter(Ticket.status == TicketStatus.open).count(),
            "in_progress": my_tickets.filter(Ticket.status == TicketStatus.in_progress).count(),
            "resolved": my_tickets.filter(Ticket.status == TicketStatus.resolved).count(),
            "closed": my_tickets.filter(Ticket.status == TicketStatus.closed).count(),
        },
        "my_chats": {
            "total": my_sessions.count(),
            "active": my_sessions.filter(ChatSession.status == ChatSessionStatus.active).count(),
        },
    }


def _admin_stats(db: Session) -> dict:
    return {
        "users": {
            "total": db.query(User).count(),
            "customers": db.query(User).filter(User.role == UserRole.customer).count(),
            "agents": db.query(User).filter(User.role == UserRole.agent).count(),
            "admins": db.query(User).filter(User.role == UserRole.admin).count(),
        },
        "tickets": {
            "total": db.query(Ticket).count(),
            "open": db.query(Ticket).filter(Ticket.status == TicketStatus.open).count(),
            "in_progress": db.query(Ticket).filter(Ticket.status == TicketStatus.in_progress).count(),
            "resolved": db.query(Ticket).filter(Ticket.status == TicketStatus.resolved).count(),
            "closed": db.query(Ticket).filter(Ticket.status == TicketStatus.closed).count(),
            "unassigned": db.query(Ticket).filter(Ticket.assigned_agent_id == None).count(),
        },
        "chat": {
            "total_sessions": db.query(ChatSession).count(),
            "active_sessions": db.query(ChatSession).filter(ChatSession.status == ChatSessionStatus.active).count(),
            "total_messages": db.query(ChatMessage).count(),
        },
        "monitoring": {
            "machines_tracked": db.query(func.count(func.distinct(HealthData.machine_id))).scalar(),
            "health_records": db.query(HealthData).count(),
            "controllers_tracked": db.query(func.count(func.distinct(NetworkData.controller_id))).scalar(),
            "network_records": db.query(NetworkData).count(),
        },
        "devices": {
            "total": db.query(Device).count(),
            "active": db.query(Device).filter(Device.is_active == True).count(),
        },
        "alerts": {
            "total": db.query(Alert).count(),
            "unresolved": db.query(Alert).filter(Alert.resolved == False).count(),
        },
        "isp": {
            "providers": db.query(ISPProvider).filter(ISPProvider.is_active == True).count(),
            "active_outages": db.query(ISPOutage).filter(ISPOutage.ended_at == None).count(),
        },
    }
