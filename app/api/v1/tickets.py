from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, Ticket, TicketStatus, TicketType

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])


class TicketCreate(BaseModel):
    ticket_type: TicketType
    description: str
    reported_user_id: Optional[int] = None
    product_id: Optional[int] = None


class TicketResponse(BaseModel):
    id: int
    user_id: int
    reported_user_id: Optional[int] = None
    product_id: Optional[int] = None
    ticket_type: str
    description: str
    status: str
    created_at: str

    model_config = {"from_attributes": True}


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_data: TicketCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    ticket = Ticket(
        user_id=current_user.id,
        ticket_type=ticket_data.ticket_type,
        description=ticket_data.description,
        reported_user_id=ticket_data.reported_user_id,
        product_id=ticket_data.product_id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("", response_model=List[TicketResponse])
def list_tickets(
    skip: int = 0,
    limit: int = 50,
    status: Optional[TicketStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(Ticket).order_by(Ticket.created_at.desc())

    if status:
        query = query.filter(Ticket.status == status)

    tickets = query.offset(skip).limit(limit).all()
    return tickets


@router.get("/my-tickets", response_model=List[TicketResponse])
def my_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    tickets = (
        db.query(Ticket)
        .filter(Ticket.user_id == current_user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )
    return tickets


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )

    if ticket.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    return ticket


@router.patch("/{ticket_id}/status")
def update_ticket_status(
    ticket_id: int,
    new_status: TicketStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )

    ticket.status = new_status
    db.commit()
    return {"message": f"Ticket status updated to {new_status.value}"}
