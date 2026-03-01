from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Ticket, User, TicketStatus, UserRole
from app.schemas import TicketCreate, TicketUpdate, TicketOut
from app.auth import get_current_user

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("/", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = Ticket(
        subject=data.subject,
        description=data.description,
        priority=data.priority,
        user_id=current_user.id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/", response_model=list[TicketOut])
def list_tickets(
    status_filter: Optional[TicketStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Ticket)

    # Customers only see their own tickets
    if current_user.role == UserRole.customer:
        query = query.filter(Ticket.user_id == current_user.id)

    if status_filter:
        query = query.filter(Ticket.status == status_filter)

    return query.order_by(Ticket.created_at.desc()).all()


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Customers can only view their own tickets
    if current_user.role == UserRole.customer and ticket.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return ticket


@router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Customers can only update their own tickets (limited fields)
    if current_user.role == UserRole.customer:
        if ticket.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        # Customers can only update subject and description
        if data.status or data.assigned_agent_id:
            raise HTTPException(status_code=403, detail="Customers cannot change status or assignment")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ticket, key, value)

    db.commit()
    db.refresh(ticket)
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.agent, UserRole.admin):
        raise HTTPException(status_code=403, detail="Only agents/admins can delete tickets")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    db.delete(ticket)
    db.commit()
